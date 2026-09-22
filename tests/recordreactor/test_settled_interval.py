"""Regression guard for #652: interval records must not be computed before rooftop lands.

Interval detection runs ~5 minutes after the interval, rooftop solar arrives 30-60 minutes later,
and nothing re-checked the interval once the data settled. Every series containing solar was
therefore recorded on a grid-only sum (`au.nem.vic1.power.interval.low` fired at 3,248 MW when the
settled value was 5,450 MW; `au.nem.sa1.renewables.proportion.interval.high` stored 196% against a
settled 111%).

Detection now stops at the last settled interval — the latest interval with rooftop rows for every
region — and re-scans a settle-lag window so a 30-minute rooftop block doesn't skip intervals.

The gate is per SERIES, not per network: only rows whose value can contain rooftop (network and
region totals, solar, renewables, renewable proportion) wait for it. Coal, gas, wind, batteries,
fossils, demand and price are complete as soon as the grid data lands and run to the last
completed interval. Day+ periods must not be delayed by any of this.
"""

from datetime import datetime, timedelta

import pytest

from opennem import settings
from opennem.recordreactor.incremental import _map_row_to_records, get_completed_periods, get_last_settled_interval
from opennem.recordreactor.metric_registry import (
    GROUPING_FUELTECH,
    GROUPING_NETWORK,
    GROUPING_REGION,
    GROUPING_RENEWABLE,
    GroupingConfig,
    MetricDefinition,
    get_metric_registry,
    row_contains_rooftop,
)
from opennem.recordreactor.queries_incremental import get_live_rooftop_network_codes, query_last_rooftop_interval
from opennem.recordreactor.schema import MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkNEM, NetworkWEM

NOW = datetime(2026, 9, 20, 12, 0)
# prod rooftop lag in fueltech_intervals_mv measured at ~1h45m on 22 Sep 2026
SETTLED = NOW - timedelta(minutes=105)


def _metric(metric: MilestoneType) -> MetricDefinition:
    return next(m for m in get_metric_registry() if m.metric == metric)


POWER = _metric(MilestoneType.power)
DEMAND = _metric(MilestoneType.demand)
PRICE = _metric(MilestoneType.price)
PROPORTION = _metric(MilestoneType.proportion)
EMISSIONS = _metric(MilestoneType.emissions)


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


def test_interval_window_spans_the_settle_lag_through_to_now() -> None:
    """One query covers both kinds of row; the settled bound is applied per row, not per query."""
    settled = NOW - timedelta(minutes=35)
    periods = {p: (s, e) for p, s, e in get_completed_periods(NOW, NetworkNEM, settled, 60)}

    start, end = periods[MilestonePeriod.interval]

    # re-scans the settle-lag window so a 30-minute rooftop block doesn't skip intervals
    assert start == settled - timedelta(minutes=60)
    # and still reaches the last completed interval for the series that don't wait on rooftop
    assert end == NOW + timedelta(minutes=NetworkNEM.interval_size)


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


GROUPING_REGION_FUELTECH = GroupingConfig(name="region_fueltech", group_by_fields=["network_region", "fueltech_group_id"])


@pytest.mark.parametrize(
    "metric_def,grouping,row",
    [
        # no fueltech filter at all — rooftop is inside the total
        (POWER, GROUPING_NETWORK, {}),
        (POWER, GROUPING_REGION, {"network_region": "VIC1"}),
        (EMISSIONS, GROUPING_REGION, {"network_region": "VIC1"}),
        # the solar rows of a fueltech query
        (POWER, GROUPING_FUELTECH, {"fueltech_group_id": "solar"}),
        (POWER, GROUPING_REGION_FUELTECH, {"network_region": "SA1", "fueltech_group_id": "solar"}),
        # the renewables rows of a renewable query
        (POWER, GROUPING_RENEWABLE, {"renewable": 1}),
        # rooftop is in both generation_renewable and demand_gross
        (PROPORTION, GROUPING_NETWORK, {}),
        (PROPORTION, GROUPING_REGION, {"network_region": "SA1"}),
    ],
)
def test_rows_that_can_contain_rooftop(metric_def, grouping, row) -> None:
    assert row_contains_rooftop(metric_def, grouping, row) is True


@pytest.mark.parametrize(
    "metric_def,grouping,row",
    [
        (POWER, GROUPING_FUELTECH, {"fueltech_group_id": "coal"}),
        (POWER, GROUPING_FUELTECH, {"fueltech_group_id": "wind"}),
        (POWER, GROUPING_FUELTECH, {"fueltech_group_id": "battery_charging"}),
        (POWER, GROUPING_REGION_FUELTECH, {"network_region": "QLD1", "fueltech_group_id": "coal"}),
        # the fossils rows of a renewable query
        (POWER, GROUPING_RENEWABLE, {"renewable": 0}),
        # operational demand excludes rooftop; price has no generation in it
        (DEMAND, GROUPING_NETWORK, {}),
        (DEMAND, GROUPING_REGION, {"network_region": "VIC1"}),
        (PRICE, GROUPING_REGION, {"network_region": "VIC1"}),
    ],
)
def test_rows_that_cannot_contain_rooftop(metric_def, grouping, row) -> None:
    assert row_contains_rooftop(metric_def, grouping, row) is False


def _map(metric_def, grouping, row, interval, settled=SETTLED):
    return _map_row_to_records(
        row={"time_bucket": interval, "interval_count": 1, **row},
        metric_def=metric_def,
        grouping=grouping,
        period=MilestonePeriod.interval,
        network=NetworkNEM,
        current_state={},
        settled_interval=settled,
    )


def test_unsettled_solar_row_is_held_back() -> None:
    records = _map(POWER, GROUPING_FUELTECH, {"fueltech_group_id": "solar", "value": 18294.0}, NOW)

    assert records == []


def test_unsettled_region_total_row_is_held_back() -> None:
    """The vic1 power interval lows of #652 came from region totals missing their rooftop."""
    records = _map(POWER, GROUPING_REGION, {"network_region": "VIC1", "value": 3248.0}, NOW)

    assert records == []


def test_unsettled_proportion_row_is_held_back() -> None:
    records = _map(PROPORTION, GROUPING_REGION, {"network_region": "SA1", "value": 196.31}, NOW)

    assert records == []


def test_unsettled_coal_row_is_detected_immediately() -> None:
    """QLD1 coal has no rooftop in it and must not wait on the rooftop lag."""
    records = _map(POWER, GROUPING_REGION_FUELTECH, {"network_region": "QLD1", "fueltech_group_id": "coal", "value": 5000.0}, NOW)

    assert [r.interval for r in records] == [NOW, NOW]  # high and low candidates


def test_unsettled_demand_and_price_rows_are_detected_immediately() -> None:
    demand = _map(DEMAND, GROUPING_NETWORK, {"value": 9072.29}, NOW)
    price = _map(PRICE, GROUPING_REGION, {"network_region": "VIC1", "value": 120.0}, NOW)

    assert demand and all(r.interval == NOW for r in demand)
    assert price and all(r.interval == NOW for r in price)


def test_unsettled_fossils_row_is_detected_immediately() -> None:
    records = _map(POWER, GROUPING_RENEWABLE, {"renewable": 0, "value": 12000.0}, NOW)

    assert records and all(r.interval == NOW for r in records)


def test_settled_solar_row_is_detected() -> None:
    """Once the interval has settled the same solar row goes through."""
    records = _map(POWER, GROUPING_FUELTECH, {"fueltech_group_id": "solar", "value": 24020.0}, SETTLED)

    assert records and all(r.interval == SETTLED for r in records)


def test_no_settled_interval_gates_nothing() -> None:
    """Without a settled interval (day+ periods, or a caller that doesn't pass one) nothing waits."""
    records = _map(POWER, GROUPING_FUELTECH, {"fueltech_group_id": "solar", "value": 24020.0}, NOW, settled=None)

    assert records and all(r.interval == NOW for r in records)
