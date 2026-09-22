"""Regression guard for #652: interval records must not be computed before rooftop lands.

Interval detection runs ~5 minutes after the interval, rooftop solar arrives 30-60 minutes later,
and nothing re-checked the interval once the data settled. Every series containing solar was
therefore recorded on a grid-only sum (`au.nem.vic1.power.interval.low` fired at 3,248 MW when the
settled value was 5,450 MW; `au.nem.sa1.renewables.proportion.interval.high` stored 196% against a
settled 111%).

Detection now stops at the last settled interval — the latest interval with rooftop rows for every
region — and re-scans a settle-lag window so a 30-minute rooftop block doesn't skip intervals.
Day+ periods must not be delayed by any of this.
"""

from datetime import datetime, timedelta

from opennem import settings
from opennem.recordreactor.incremental import get_completed_periods, get_last_settled_interval
from opennem.recordreactor.queries_incremental import get_live_rooftop_network_codes, query_last_rooftop_interval
from opennem.recordreactor.schema import MilestonePeriod
from opennem.schema.network import NetworkNEM, NetworkWEM

NOW = datetime(2026, 9, 20, 12, 0)


class _StubClient:
    """Returns a fixed rooftop result set, or raises."""

    def __init__(self, rows: list[tuple[str, datetime]] | None = None, raises: bool = False) -> None:
        self.rows = rows or []
        self.raises = raises
        self.queries: list[str] = []

    def execute(self, query: str) -> list[tuple[str, datetime]]:
        self.queries.append(query)
        if self.raises:
            raise RuntimeError("clickhouse is down")
        return self.rows


def _nem_rooftop_rows(last: datetime, laggard: datetime | None = None) -> list[tuple[str, datetime]]:
    rows = [(region, last) for region in NetworkNEM.regions or []]
    if laggard is not None:
        rows[-1] = (rows[-1][0], laggard)
    return rows


def test_live_rooftop_codes_exclude_backfill_networks() -> None:
    """The backfill subnetwork stopped years ago — its max interval must not peg settledness."""
    codes = get_live_rooftop_network_codes(NetworkNEM)

    assert codes == ["AEMO_ROOFTOP"]
    assert "OPENNEM_ROOFTOP_BACKFILL" not in codes
    # WEM rooftop comes from APVI
    assert get_live_rooftop_network_codes(NetworkWEM) == ["APVI"]


def test_rooftop_interval_is_the_slowest_region() -> None:
    """One lagging region holds the whole network back — its interval is the settled one."""
    client = _StubClient(_nem_rooftop_rows(last=NOW - timedelta(minutes=30), laggard=NOW - timedelta(minutes=45)))

    assert query_last_rooftop_interval(client, NetworkNEM, NOW) == NOW - timedelta(minutes=45)
    assert "'AEMO_ROOFTOP'" in client.queries[0]
    assert "fueltech_intervals_mv" in client.queries[0]


def test_rooftop_interval_none_when_a_region_is_missing() -> None:
    """Four regions reporting must not declare the interval settled for all five."""
    rows = _nem_rooftop_rows(last=NOW - timedelta(minutes=30))[:-1]
    client = _StubClient(rows)

    assert query_last_rooftop_interval(client, NetworkNEM, NOW) is None


def test_settled_interval_falls_back_to_lag_on_query_failure(monkeypatch) -> None:
    monkeypatch.setattr(settings, "milestone_interval_settle_lag_minutes", 60)
    client = _StubClient(raises=True)

    assert get_last_settled_interval(client, NetworkNEM, NOW) == NOW - timedelta(minutes=60)


def test_settled_interval_never_runs_ahead_of_now(monkeypatch) -> None:
    """Rooftop reporting past the last completed interval can't pull detection forward."""
    monkeypatch.setattr(settings, "milestone_interval_settle_lag_minutes", 60)
    client = _StubClient(_nem_rooftop_rows(last=NOW + timedelta(minutes=30)))

    assert get_last_settled_interval(client, NetworkNEM, NOW) == NOW


def test_settled_interval_uses_rooftop_when_available(monkeypatch) -> None:
    monkeypatch.setattr(settings, "milestone_interval_settle_lag_minutes", 60)
    client = _StubClient(_nem_rooftop_rows(last=NOW - timedelta(minutes=35)))

    assert get_last_settled_interval(client, NetworkNEM, NOW) == NOW - timedelta(minutes=35)


def test_interval_period_stops_at_the_settled_interval() -> None:
    settled = NOW - timedelta(minutes=35)
    periods = {p: (s, e) for p, s, e in get_completed_periods(NOW, NetworkNEM, settled, 60)}

    start, end = periods[MilestonePeriod.interval]

    # window ends on the settled interval (end is exclusive, one interval past it)
    assert end == settled + timedelta(minutes=NetworkNEM.interval_size)
    assert end <= NOW
    # and re-scans the settle-lag window so a 30-minute rooftop block doesn't skip intervals
    assert start == settled - timedelta(minutes=60)


def test_interval_period_unchanged_without_a_settled_interval() -> None:
    """Default (no settled interval supplied) keeps the single-interval window at now."""
    periods = {p: (s, e) for p, s, e in get_completed_periods(NOW, NetworkNEM)}

    assert periods[MilestonePeriod.interval] == (NOW, NOW + timedelta(minutes=NetworkNEM.interval_size))


def test_day_and_above_are_not_delayed_by_settledness() -> None:
    """Day+ periods keep using `now` — a rooftop lag must not hold a day record back a day."""
    settled = NOW - timedelta(hours=6)

    gated = {p: (s, e) for p, s, e in get_completed_periods(NOW, NetworkNEM, settled, 60)}
    ungated = {p: (s, e) for p, s, e in get_completed_periods(NOW, NetworkNEM)}

    for period in (MilestonePeriod.day, MilestonePeriod.month, MilestonePeriod.quarter, MilestonePeriod.year):
        assert gated[period] == ungated[period]

    assert gated[MilestonePeriod.day] == (datetime(2026, 9, 19), datetime(2026, 9, 20))


def test_wem_settles_on_apvi_rooftop(monkeypatch) -> None:
    """WEM has a single region fed by APVI — the same derivation must work there."""
    monkeypatch.setattr(settings, "milestone_interval_settle_lag_minutes", 60)
    client = _StubClient([("WEM", NOW - timedelta(minutes=20))])

    assert get_last_settled_interval(client, NetworkWEM, NOW) == NOW - timedelta(minutes=20)
    assert "'APVI'" in client.queries[0]
