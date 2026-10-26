"""task_nem_interval_check ordering and failure isolation (#726)."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from opennem.tasks import tasks

_real_sleep = asyncio.sleep  # tasks.asyncio is the global module: _run patches asyncio.sleep


def _run(crawl_fn, aggregate=None, export=None, events=None):
    events = events if events is not None else []

    async def _agg() -> int:
        events.append("agg")
        return 0

    async def _exp(network) -> None:
        events.append(f"export:{network.code}")

    async def _noop(**_: object) -> None:
        return None

    async def _sleep(_: float) -> None:
        return None

    with (
        patch.object(tasks, "run_crawl", AsyncMock(side_effect=crawl_fn)),
        patch.object(tasks.asyncio, "sleep", _sleep),
        patch.object(tasks, "process_energy_last_intervals", AsyncMock(side_effect=lambda **_: events.append("energy"))),
        patch.object(
            tasks, "run_market_summary_aggregate_for_last_intervals", AsyncMock(side_effect=lambda **_: events.append("market"))
        ),
        patch.object(tasks, "run_unit_intervals_aggregate_to_now", aggregate or _agg),
        patch.object(tasks, "run_export_power_latest_for_network", export or (lambda network: _exp(network))),
    ):
        asyncio.run(tasks.task_nem_interval_check({}))
    return events


def _ok(crawler, **_):
    return SimpleNamespace(inserted_records=5)


def test_aggregate_completes_before_exports_start() -> None:
    events = _run(_ok)
    assert events == ["energy", "market", "agg", f"export:{tasks.NetworkNEM.code}", f"export:{tasks.NetworkAU.code}"]


def test_price_crawl_starts_before_scada_poll_and_is_sequential() -> None:
    order: list[str] = []

    async def _crawl(crawler, **_):
        order.append(crawler.name)
        await _real_sleep(0)  # real loop yield, as a network call would
        return SimpleNamespace(inserted_records=1)

    _run(_crawl)
    # both start in the first loop tick: the price crawl does not wait for SCADA to land
    assert set(order[:2]) == {tasks.AEMONemwebDispatchIS.name, tasks.AEMONNemwebDispatchScada.name}
    assert order.index(tasks.AEMONemwebTradingIS.name) > order.index(tasks.AEMONemwebDispatchIS.name)
    assert tasks.AEMONNemwebDispatchScada.name in order
    # early dispatch crawl found records: no second price crawl
    assert order.count(tasks.AEMONemwebDispatchIS.name) == 1


def test_price_crawl_repeated_when_dispatch_published_after_early_crawl() -> None:
    order: list[str] = []

    async def _crawl(crawler, **_):
        order.append(crawler.name)
        # the first DispatchIS crawl finds nothing new; scada lands
        n = 0 if (crawler is tasks.AEMONemwebDispatchIS and order.count(crawler.name) == 1) else 3
        return SimpleNamespace(inserted_records=n)

    _run(_crawl)
    assert order.count(tasks.AEMONemwebDispatchIS.name) == 2


def test_price_crawl_failure_does_not_kill_scada_or_exports() -> None:
    async def _crawl(crawler, **_):
        if crawler in (tasks.AEMONemwebDispatchIS, tasks.AEMONemwebTradingIS):
            raise RuntimeError("proxy down")
        return SimpleNamespace(inserted_records=5)

    events = _run(_crawl)
    assert events[-3:] == ["agg", f"export:{tasks.NetworkNEM.code}", f"export:{tasks.NetworkAU.code}"]


def test_aggregate_failure_still_exports_then_raises() -> None:
    events: list[str] = []

    async def _bad() -> int:
        events.append("agg")
        raise RuntimeError("pg down")

    with pytest.raises(RuntimeError, match="pg down"):
        _run(_ok, aggregate=_bad, events=events)
    assert events[-2:] == [f"export:{tasks.NetworkNEM.code}", f"export:{tasks.NetworkAU.code}"]


def test_rooftop_crawl_with_nothing_new_does_not_retry() -> None:
    with patch.object(tasks, "run_crawl", AsyncMock(return_value=SimpleNamespace(inserted_records=0))) as crawl:
        asyncio.run(tasks.task_nem_rooftop_crawl({"job_try": 1}))  # used to raise arq.Retry
    assert crawl.await_count == 2


def test_hung_aggregate_is_capped_and_exports_still_run() -> None:
    events: list[str] = []

    async def _hang() -> int:
        await _real_sleep(3600)
        return 0

    with patch.object(tasks, "NEM_AGGREGATE_BUDGET_SECONDS", 0.01), pytest.raises(TimeoutError):
        _run(_ok, aggregate=_hang, events=events)
    assert events[-2:] == [f"export:{tasks.NetworkNEM.code}", f"export:{tasks.NetworkAU.code}"]


def test_cancelled_poll_cancels_price_crawl() -> None:
    seen: dict[str, bool] = {}

    async def _crawl(crawler, **_):
        if crawler is tasks.AEMONemwebDispatchIS:
            try:
                await _real_sleep(3600)
            except asyncio.CancelledError:
                seen["cancelled"] = True
                raise
        await _real_sleep(0)  # let the price crawl start
        raise asyncio.CancelledError  # job cancelled during the SCADA poll

    with pytest.raises(asyncio.CancelledError):
        _run(_crawl)
    assert seen == {"cancelled": True}
