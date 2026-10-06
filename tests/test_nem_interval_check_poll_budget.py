"""The SCADA poll stops at its budget so prices, aggregates and exports still run."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from opennem.tasks import tasks


def test_poll_budget_leaves_time_for_the_rest_of_the_pipeline() -> None:
    clock = [0.0]

    async def _crawl(crawler: object, **kwargs: object) -> SimpleNamespace:
        if crawler is tasks.AEMONNemwebDispatchScada:
            clock[0] += 50  # each poll is slow and finds nothing
            return SimpleNamespace(inserted_records=0)
        return SimpleNamespace(inserted_records=5)

    async def _sleep(seconds: float) -> None:
        clock[0] += seconds

    crawl = AsyncMock(side_effect=_crawl)
    with (
        patch.object(tasks, "run_crawl", crawl),
        patch.object(tasks.asyncio, "sleep", _sleep),
        patch.object(tasks.time, "monotonic", lambda: clock[0]),
        patch.object(tasks, "process_energy_last_intervals", AsyncMock()) as energy,
        patch.object(tasks, "run_market_summary_aggregate_for_last_intervals", AsyncMock()) as market,
        patch.object(tasks, "run_unit_intervals_aggregate_to_now", AsyncMock()),
        patch.object(tasks, "run_export_power_latest_for_network", AsyncMock()) as export,
    ):
        asyncio.run(tasks.task_nem_interval_check({}))

    crawlers = [c.args[0] for c in crawl.await_args_list]
    # polls end at 50s, 105s and 165s; waiting again after the third would pass the 120s budget
    assert crawlers == [
        tasks.AEMONNemwebDispatchScada,
        tasks.AEMONNemwebDispatchScada,
        tasks.AEMONNemwebDispatchScada,
        tasks.AEMONemwebDispatchIS,
        tasks.AEMONemwebTradingIS,
    ]
    energy.assert_awaited_once()
    market.assert_awaited_once()
    assert export.await_count == 2
