"""task_wem_day_crawl exports only the years its crawl window touches.

With no year it re-exported every WEM year since 2006 each hour and logged errors for the years
before WEM market data exists.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from opennem.tasks import tasks


@asynccontextmanager
async def _fake_session():
    yield None


def _run(now: datetime) -> AsyncMock:
    export_energy = AsyncMock()
    with (
        patch.object(tasks, "run_all_wem_crawlers", AsyncMock()),
        patch.object(tasks, "get_last_completed_interval_for_network", return_value=now),
        patch.object(tasks, "get_write_session", _fake_session),
        patch.object(tasks, "process_unit_intervals_backlog", AsyncMock()),
        patch.object(tasks, "run_export_power_latest_for_network", AsyncMock()),
        patch.object(tasks, "run_export_energy_for_year", export_energy),
    ):
        asyncio.run(tasks.task_wem_day_crawl({}))
    return export_energy


@pytest.mark.parametrize(
    ("now", "years"),
    [
        (datetime(2026, 10, 6, 9, 30), [2026]),
        # the 2-day window still covers the last days of the old year
        (datetime(2027, 1, 1, 0, 30), [2026, 2027]),
        (datetime(2027, 1, 2, 23, 55), [2026, 2027]),
        (datetime(2027, 1, 3, 0, 5), [2027]),
    ],
)
def test_exports_only_the_window_years(now: datetime, years: list[int]) -> None:
    export_energy = _run(now)

    assert [c.kwargs["year"] for c in export_energy.await_args_list] == years
    assert all(c.kwargs["network"].code == "WEM" for c in export_energy.await_args_list)
