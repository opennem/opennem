"""Cheap SCADA listing poll: full crawl only when a new file is listed."""

import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from opennem.tasks import tasks
from opennem.utils.ingest_latency import IngestTrace

_real_sleep = asyncio.sleep
LAST = datetime(2026, 11, 5, 10, 25)
NEW = datetime(2026, 11, 5, 10, 30)


@pytest.fixture(autouse=True)
def _reset_state():
    tasks._last_scada_interval = LAST
    yield
    tasks._last_scada_interval = None


def _run(listing: list, scada_inserted: int = 5, clock: list[float] | None = None):
    """Run the task; `listing` is the sequence of newest-listed intervals (last repeats), returns (crawl, listing mocks)"""
    clock = clock if clock is not None else [0.0]
    calls = {"n": 0}

    async def _listed(url: str):
        i = min(calls["n"], len(listing) - 1)
        calls["n"] += 1
        clock[0] += 0.1
        value = listing[i]
        if isinstance(value, Exception):
            raise value
        return value

    async def _crawl(crawler: object, **kwargs: object) -> SimpleNamespace:
        if crawler is tasks.AEMONNemwebDispatchScada:
            return SimpleNamespace(inserted_records=scada_inserted, interval_max=NEW)
        return SimpleNamespace(inserted_records=1)

    async def _sleep(seconds: float) -> None:
        clock[0] += seconds

    crawl = AsyncMock(side_effect=_crawl)
    listing_mock = AsyncMock(side_effect=_listed)
    with (
        patch.object(tasks, "get_newest_listed_interval", listing_mock),
        patch.object(tasks, "run_crawl", crawl),
        patch.object(tasks.asyncio, "sleep", _sleep),
        patch.object(tasks.time, "monotonic", lambda: clock[0]),
        patch.object(tasks, "process_energy_last_intervals", AsyncMock()),
        patch.object(tasks, "run_market_summary_aggregate_for_last_intervals", AsyncMock()),
        patch.object(tasks, "run_unit_intervals_aggregate_to_now", AsyncMock()),
        patch.object(tasks, "run_export_power_latest_for_network", AsyncMock()),
    ):
        asyncio.run(tasks.task_nem_interval_check({}))
    return crawl, listing_mock, clock


def _scada_crawls(crawl: AsyncMock) -> int:
    return sum(1 for c in crawl.await_args_list if c.args[0] is tasks.AEMONNemwebDispatchScada)


def test_no_new_file_means_no_full_scada_crawl() -> None:
    crawl, listing, clock = _run([LAST])
    assert _scada_crawls(crawl) == 0
    assert listing.await_count > 10  # fast polls, then backoff, until the budget is spent
    assert clock[0] <= tasks.NEM_SCADA_POLL_BUDGET_SECONDS + 1


def test_new_file_triggers_exactly_one_full_crawl() -> None:
    crawl, listing, _ = _run([LAST, LAST, NEW])
    assert _scada_crawls(crawl) == 1
    assert listing.await_count == 3
    assert tasks._last_scada_interval == NEW


def test_fast_poll_cadence_then_backoff() -> None:
    sleeps: list[float] = []
    clock = [0.0]

    async def _sleep(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    async def _listed(url: str) -> datetime:
        clock[0] += 0.1
        return LAST

    with (
        patch.object(tasks, "get_newest_listed_interval", AsyncMock(side_effect=_listed)),
        patch.object(tasks, "run_crawl", AsyncMock(return_value=SimpleNamespace(inserted_records=1))),
        patch.object(tasks.asyncio, "sleep", _sleep),
        patch.object(tasks.time, "monotonic", lambda: clock[0]),
        patch.object(tasks, "process_energy_last_intervals", AsyncMock()),
        patch.object(tasks, "run_market_summary_aggregate_for_last_intervals", AsyncMock()),
        patch.object(tasks, "run_unit_intervals_aggregate_to_now", AsyncMock()),
        patch.object(tasks, "run_export_power_latest_for_network", AsyncMock()),
    ):
        asyncio.run(tasks.task_nem_interval_check({}))

    assert sleeps[0] == tasks.NEM_SCADA_FAST_POLL_SECONDS
    assert sleeps[-1] != tasks.NEM_SCADA_FAST_POLL_SECONDS
    slow = [s for s in sleeps if s != tasks.NEM_SCADA_FAST_POLL_SECONDS]
    assert slow == tasks.NEM_SCADA_SLOW_BACKOFF[: len(slow)]


def test_unknown_baseline_falls_back_to_full_crawl() -> None:
    tasks._last_scada_interval = None
    crawl, _, _ = _run([NEW])
    assert _scada_crawls(crawl) == 1


def test_listing_error_falls_back_to_full_crawl() -> None:
    crawl, _, _ = _run([RuntimeError("boom")])
    assert _scada_crawls(crawl) == 1


def test_failed_full_crawl_keeps_baseline_so_next_poll_retries() -> None:
    crawl, _, _ = _run([NEW], scada_inserted=0)
    assert _scada_crawls(crawl) > 1  # inserted 0 never advances the baseline
    assert tasks._last_scada_interval == LAST


def test_poll_exception_cancels_prices_task() -> None:
    cancelled: list[bool] = []

    async def _crawl(crawler: object, **kwargs: object) -> SimpleNamespace:
        if crawler is tasks.AEMONNemwebDispatchScada:
            await _real_sleep(0.05)  # let the prices task start and park
            raise RuntimeError("scada boom")
        try:
            await asyncio.sleep(10)  # real sleep: stays pending until cancelled
        except asyncio.CancelledError:
            cancelled.append(True)
            raise
        return SimpleNamespace(inserted_records=1)

    with (
        patch.object(tasks, "get_newest_listed_interval", AsyncMock(return_value=NEW)),
        patch.object(tasks, "run_crawl", AsyncMock(side_effect=_crawl)),
        pytest.raises(RuntimeError, match="scada boom"),
    ):
        asyncio.run(tasks.task_nem_interval_check({}))

    assert cancelled == [True]


def test_trace_parses_file_generation_time() -> None:
    trace = IngestTrace()
    trace.boundary = datetime(2026, 11, 5, 10, 30).replace(tzinfo=tasks_tz()).timestamp()
    trace.set_file_generated(b"C,NEMP.WORLD,DISPATCHSCADA,AEMO,PUBLIC,2026/11/05,10:30:18,0000000512345678,DISPATCHSCADA\nI,x")
    assert trace.file_generated == 18.0


def tasks_tz():
    from opennem.utils.ingest_latency import _NEM_TZ

    return _NEM_TZ
