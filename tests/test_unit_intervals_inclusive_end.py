"""unit_intervals incremental aggregate publishes the last settled interval (#726).

The final output filter was `cd.interval < :end_time`, so with end = last completed interval the newest
bucket was never written: ch trailed postgres scada by one 5 min interval (dev: CH 18:55, PG 19:00).
"""

import asyncio
import inspect
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from opennem.aggregates import unit_intervals as ui


def _collapse(fn) -> str:
    return " ".join(inspect.getsource(fn).split())


def test_query_gapfills_and_filters_on_exclusive_bound_param() -> None:
    src = _collapse(ui._get_unit_interval_data)
    # price + rooftop gapfill finish and the output filter share the bound; a half-open [start, end_excl)
    assert "time_bucket_gapfill('5 minutes', pd.interval, :start_time, :end_excl)" in src
    assert "time_bucket_gapfill('5 minutes', fs.interval, :solar_start_time, :end_excl)" in src
    assert "AND cd.interval < :end_excl" in src
    # source scans still read the end bucket
    assert "AND fs.interval <= :end_time" in src


def _params_for(inclusive_end: bool) -> dict:
    session = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = []
    session.execute = AsyncMock(return_value=result)
    start, end = datetime(2026, 10, 12, 18, 50), datetime(2026, 10, 12, 18, 55)
    asyncio.run(ui._get_unit_interval_data(session, start, end, inclusive_end=inclusive_end))
    return session.execute.await_args.args[1]


def test_inclusive_end_extends_exclusive_bound_by_one_interval() -> None:
    inc = _params_for(True)
    assert inc["end_time"] == datetime(2026, 10, 12, 18, 55)
    assert inc["end_excl"] == datetime(2026, 10, 12, 19, 0)  # bucket 18:55 is emitted


def test_default_stays_half_open_for_backlog_chunks() -> None:
    exc = _params_for(False)
    assert exc["end_excl"] == exc["end_time"]  # adjacent chunks must not overlap


def _run_to_now(max_interval: datetime, now: datetime, rows: list[tuple]):
    get_data = AsyncMock(return_value=rows)
    insert = AsyncMock()
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    session_cm.__aexit__ = AsyncMock(return_value=False)
    with (
        patch.object(ui, "get_clickhouse_client", MagicMock()),
        patch.object(ui, "execute_async", AsyncMock(return_value=[(max_interval,)])),
        patch.object(ui, "get_last_completed_interval_for_network", lambda **_: now),
        patch.object(ui, "get_write_session", MagicMock(return_value=session_cm)),
        patch.object(ui, "_get_unit_interval_data", get_data),
        patch.object(ui, "_prepare_unit_interval_data", lambda r: list(r)),
        patch.object(ui, "insert_async", insert),
    ):
        n = asyncio.run(ui.run_unit_intervals_aggregate_to_now())
    return n, get_data, insert


def test_aggregate_to_now_requests_inclusive_end_and_logs_max_interval(caplog) -> None:
    now = datetime(2026, 10, 12, 18, 55)
    rows = [(datetime(2026, 10, 12, 18, 55), "NEM"), (datetime(2026, 10, 12, 19, 0), "WEM")]
    # opennem loggers don't propagate: attach caplog's handler directly
    ui.logger.addHandler(caplog.handler)
    ui.logger.setLevel("INFO")
    try:
        n, get_data, insert = _run_to_now(datetime(2026, 10, 12, 18, 50), now, rows)
    finally:
        ui.logger.removeHandler(caplog.handler)
    # ch max 18:50, last completed 18:55 -> exactly one interval (18:55), written this cycle
    assert get_data.await_args.args[1:3] == (datetime(2026, 10, 12, 18, 55), now)
    assert get_data.await_args.kwargs == {"inclusive_end": True}
    assert n == 2
    insert.assert_awaited_once()
    assert "max interval written 2026-10-12 18:55:00" in caplog.text
    assert caplog.records


def test_aggregate_to_now_noop_when_ch_is_current() -> None:
    now = datetime(2026, 10, 12, 18, 55)
    n, get_data, insert = _run_to_now(now, now, [])
    assert n == 0
    get_data.assert_not_awaited()
    insert.assert_not_awaited()


def test_partial_interval_is_rewritten_by_later_aggregation() -> None:
    """Re-insert of the same (interval, unit) key is safe: ReplacingMergeTree(version) keeps the newest."""
    from opennem.db.clickhouse.schema import UNIT_INTERVALS_TABLE_SCHEMA as schema

    assert "ReplacingMergeTree(version)" in schema
    assert "ORDER BY (interval, network_id, network_region, facility_code, unit_code)" in schema
