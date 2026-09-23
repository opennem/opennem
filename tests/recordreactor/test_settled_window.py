"""Regression guard for #662: the interval window starts from the last settled interval covered.

The window used to be `[settled - settle lag, now]`. When the settled interval jumped further than
the lag between two runs (a worker restart, a slow rooftop crawl, rooftop landing in a batch) the
intervals in between were never checked with rooftop in them — dev missed QLD1 renewables at
8,360.7 MW on 2026-09-22 12:30, above the 8,274 MW head of its chain, and no record was written.

The last settled interval each network's pass covered is now kept in the crawl_meta watermark next
to `last_run_at`, and the next window starts from it, capped at
`milestone_interval_max_catchup_hours` so a stale watermark can't become a full scan.
"""

from datetime import datetime, timedelta

import pytest

from opennem import settings
from opennem.recordreactor import incremental, watermark
from opennem.recordreactor.incremental import get_completed_periods, get_interval_window_start
from opennem.recordreactor.schema import MilestonePeriod
from opennem.recordreactor.watermark import (
    LAST_RUN_FIELD,
    LAST_SETTLED_FIELD,
    merge_settled_intervals,
    parse_settled_intervals,
)
from opennem.schema.network import NetworkNEM, NetworkWEM

NOW = datetime(2026, 9, 22, 14, 0)
SETTLED = NOW - timedelta(minutes=30)
LOOKBACK = 60
CATCHUP_HOURS = 24


def _interval_window(settled: datetime, last_settled: datetime | None) -> tuple[datetime, datetime]:
    periods = {
        p: (s, e)
        for p, s, e in get_completed_periods(
            NOW,
            NetworkNEM,
            settled,
            LOOKBACK,
            last_settled_interval=last_settled,
            max_catchup_hours=CATCHUP_HOURS,
        )
    }
    return periods[MilestonePeriod.interval]


def test_window_starts_at_the_stored_settled_interval_when_older_than_the_lookback() -> None:
    """The #662 case: settled jumped from 11:00 to 13:30 between runs; 11:00-12:30 must be scanned."""
    last_settled = datetime(2026, 9, 22, 11, 0)

    start, end = _interval_window(SETTLED, last_settled)

    assert start == last_settled
    assert end == NOW + timedelta(minutes=NetworkNEM.interval_size)


def test_window_keeps_the_lookback_when_the_stored_value_is_recent() -> None:
    """A watermark inside the lookback doesn't shrink the re-scan."""
    start, _ = _interval_window(SETTLED, SETTLED - timedelta(minutes=10))

    assert start == SETTLED - timedelta(minutes=LOOKBACK)


def test_window_ignores_a_stored_value_ahead_of_the_settled_interval() -> None:
    """Settled can regress to the fixed-lag fallback; the window still starts at the lookback."""
    start, _ = _interval_window(SETTLED, SETTLED + timedelta(minutes=20))

    assert start == SETTLED - timedelta(minutes=LOOKBACK)


def test_missing_watermark_falls_back_to_the_lookback() -> None:
    """A row written before #662 has no settled interval: today's lookback applies."""
    start, _ = _interval_window(SETTLED, None)

    assert start == SETTLED - timedelta(minutes=LOOKBACK)


def test_catchup_is_capped() -> None:
    """Days of downtime must not turn the 5-minute cron into a full scan — that's the gap backfill's job."""
    start, _ = _interval_window(SETTLED, SETTLED - timedelta(days=5))

    assert start == SETTLED - timedelta(hours=CATCHUP_HOURS)


def test_window_start_helper_never_starts_after_the_lookback() -> None:
    for last in (None, SETTLED, SETTLED - timedelta(hours=2), SETTLED - timedelta(days=3)):
        start = get_interval_window_start(SETTLED, last, lookback_minutes=LOOKBACK, max_catchup_hours=CATCHUP_HOURS)
        assert SETTLED - timedelta(hours=CATCHUP_HOURS) <= start <= SETTLED - timedelta(minutes=LOOKBACK)


def test_day_and_above_ignore_the_watermark() -> None:
    gated = {p: (s, e) for p, s, e in get_completed_periods(NOW, NetworkNEM, SETTLED, LOOKBACK, SETTLED - timedelta(hours=6))}
    ungated = {p: (s, e) for p, s, e in get_completed_periods(NOW, NetworkNEM)}

    for period in (MilestonePeriod.day, MilestonePeriod.month, MilestonePeriod.quarter, MilestonePeriod.year):
        assert gated[period] == ungated[period]


def test_stored_value_never_moves_backwards() -> None:
    stored = {"NEM": "2026-09-22T13:30:00", "WEM": "2026-09-22T11:00:00"}
    covered = {"NEM": datetime(2026, 9, 22, 12, 0), "WEM": datetime(2026, 9, 22, 11, 30)}

    merged = merge_settled_intervals(stored, covered)

    # NEM regressed to the fallback this pass: keep what was covered before
    assert merged["NEM"] == "2026-09-22T13:30:00"
    # WEM advanced
    assert merged["WEM"] == "2026-09-22T11:30:00"


def test_merge_keeps_networks_the_pass_did_not_cover() -> None:
    merged = merge_settled_intervals({"WEM": "2026-09-22T11:00:00"}, {"NEM": datetime(2026, 9, 22, 13, 0)})

    assert merged == {"WEM": "2026-09-22T11:00:00", "NEM": "2026-09-22T13:00:00"}


@pytest.mark.parametrize("stored", [None, "not a dict", {}, {"NEM": "garbage"}])
def test_merge_tolerates_absent_or_bad_stored_values(stored) -> None:
    merged = merge_settled_intervals(stored, {"NEM": datetime(2026, 9, 22, 13, 0)})

    assert merged == {"NEM": "2026-09-22T13:00:00"}


def test_parse_drops_unreadable_entries() -> None:
    assert parse_settled_intervals({"NEM": "2026-09-22T13:00:00", "WEM": None, "X": "nope"}) == {
        "NEM": datetime(2026, 9, 22, 13, 0)
    }


class _Row:
    def __init__(self, data: dict | None) -> None:
        self.data = data


class _FakeSession:
    """Just enough of an async session for the watermark upsert."""

    def __init__(self, row: _Row | None) -> None:
        self.row = row
        self.added: list = []
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, _query):
        row = self.row

        class _Result:
            def scalar_one_or_none(self):
                return row

        return _Result()

    def add(self, row) -> None:
        self.added.append(row)

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_run_and_settled_intervals_are_one_upsert(monkeypatch) -> None:
    """Both fields land in one write, the existing keys survive, and settled only moves forward."""
    row = _Row(
        {
            LAST_RUN_FIELD: "2026-09-22T13:55:00",
            "gap_backfill_enqueued_at": "2026-09-20T00:00:00",
            LAST_SETTLED_FIELD: {"NEM": "2026-09-22T13:30:00"},
        }
    )
    sessions: list[_FakeSession] = []

    def _session():
        session = _FakeSession(row)
        sessions.append(session)
        return session

    monkeypatch.setattr(watermark, "get_write_session", _session)

    await watermark.set_last_incremental_run(
        NOW,
        settled_intervals={"NEM": datetime(2026, 9, 22, 13, 0), "WEM": datetime(2026, 9, 22, 12, 0)},
    )

    assert len(sessions) == 1 and sessions[0].commits == 1
    assert row.data == {
        LAST_RUN_FIELD: NOW.isoformat(),
        "gap_backfill_enqueued_at": "2026-09-20T00:00:00",
        LAST_SETTLED_FIELD: {"NEM": "2026-09-22T13:30:00", "WEM": "2026-09-22T12:00:00"},
    }


@pytest.mark.asyncio
async def test_run_without_settled_intervals_leaves_the_field_alone(monkeypatch) -> None:
    row = _Row({LAST_SETTLED_FIELD: {"NEM": "2026-09-22T13:30:00"}})
    monkeypatch.setattr(watermark, "get_write_session", lambda: _FakeSession(row))

    await watermark.set_last_incremental_run(NOW)

    assert row.data == {LAST_RUN_FIELD: NOW.isoformat(), LAST_SETTLED_FIELD: {"NEM": "2026-09-22T13:30:00"}}


@pytest.mark.asyncio
async def test_settled_intervals_read_back_per_network(monkeypatch) -> None:
    row = _Row({LAST_SETTLED_FIELD: {"NEM": "2026-09-22T13:30:00"}})
    monkeypatch.setattr(watermark, "get_read_session", lambda: _FakeSession(row))

    assert await watermark.get_last_settled_intervals() == {"NEM": datetime(2026, 9, 22, 13, 30)}


@pytest.mark.asyncio
async def test_settled_intervals_absent_before_662(monkeypatch) -> None:
    row = _Row({LAST_RUN_FIELD: "2026-09-22T13:55:00"})
    monkeypatch.setattr(watermark, "get_read_session", lambda: _FakeSession(row))

    assert await watermark.get_last_settled_intervals() == {}


def _patch_pass(monkeypatch, stored: dict[str, datetime], settled: datetime):
    """An incremental pass with ClickHouse and Postgres stubbed; returns (windows, writes)."""
    windows: list[tuple[str, datetime, datetime]] = []
    writes: list[tuple[datetime, dict | None]] = []

    async def _no_rebuild(caller: str) -> bool:
        return False

    async def _no_gap() -> None:
        return None

    async def _no_state() -> dict:
        return {}

    async def _stored() -> dict[str, datetime]:
        return stored

    async def _record(when: datetime, settled_intervals: dict | None = None) -> None:
        writes.append((when, settled_intervals))

    def _query(**kwargs):
        if kwargs["period"] == MilestonePeriod.interval:
            windows.append((kwargs["network"].code, kwargs["period_start"], kwargs["period_end"]))
        return []

    monkeypatch.setattr(settings, "milestone_interval_settle_lag_minutes", LOOKBACK)
    monkeypatch.setattr(settings, "milestone_interval_max_catchup_hours", CATCHUP_HOURS)
    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _no_rebuild)
    monkeypatch.setattr(incremental, "_enqueue_gap_backfill_if_needed", _no_gap)
    monkeypatch.setattr(incremental, "get_clickhouse_client", lambda: object())
    monkeypatch.setattr(incremental, "refresh_current_milestone_state", _no_state)
    monkeypatch.setattr(incremental, "get_last_settled_intervals", _stored)
    monkeypatch.setattr(incremental, "get_last_settled_interval", lambda **kwargs: settled)
    monkeypatch.setattr(incremental, "query_all_groupings_for_period", _query)
    monkeypatch.setattr(incremental, "get_last_completed_interval_for_network", lambda *a, **k: NOW + timedelta(minutes=5))
    monkeypatch.setattr(incremental, "set_last_incremental_run", _record)

    return windows, writes


@pytest.mark.asyncio
async def test_pass_scans_from_the_stored_settled_interval_and_records_the_new_one(monkeypatch) -> None:
    last = datetime(2026, 9, 22, 11, 0)
    windows, writes = _patch_pass(monkeypatch, {"NEM": last}, SETTLED)

    await incremental.run_incremental_milestone_check(networks=[NetworkNEM, NetworkWEM], alert_slack=False)

    starts = {code: start for code, start, _ in windows}
    assert starts["NEM"] == last
    # WEM has no stored value yet: today's lookback
    assert starts["WEM"] == SETTLED - timedelta(minutes=LOOKBACK)
    # one write at the end, carrying the settled interval each network covered
    assert writes == [(NOW + timedelta(minutes=5), {"NEM": SETTLED, "WEM": SETTLED})]


@pytest.mark.asyncio
async def test_a_pass_that_fails_does_not_advance_the_settled_interval(monkeypatch) -> None:
    """Persisting failed part way: the next pass must re-cover the same intervals."""
    _, writes = _patch_pass(monkeypatch, {"NEM": datetime(2026, 9, 22, 11, 0)}, SETTLED)

    def _boom(**kwargs):
        raise RuntimeError("clickhouse went away")

    monkeypatch.setattr(incremental, "query_all_groupings_for_period", _boom)

    with pytest.raises(RuntimeError):
        await incremental.run_incremental_milestone_check(networks=[NetworkNEM], alert_slack=False)

    assert writes == []
