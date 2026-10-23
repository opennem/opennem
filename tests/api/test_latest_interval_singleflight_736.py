"""#736: concurrent cold requests share one max(interval) query."""

import asyncio
from datetime import datetime
from unittest.mock import patch

import pytest

from opennem.api import intervals
from opennem.api.queries import QueryType
from opennem.core.networks import network_from_network_code

pytestmark = pytest.mark.asyncio


async def test_concurrent_misses_run_one_query() -> None:
    intervals._latest_interval_cache.clear()
    calls: list[str] = []

    async def fake_execute(client, query, params=None):
        calls.append(query)
        await asyncio.sleep(0.05)
        return [(datetime(2026, 1, 1, 12, 0),)]

    network = network_from_network_code("NEM")
    with patch.object(intervals, "execute_async", fake_execute):
        out = await asyncio.gather(
            *(intervals.cap_date_end_to_settled_interval(None, network, QueryType.DATA, datetime(2026, 1, 2)) for _ in range(10))
        )
        await intervals.cap_date_end_to_settled_interval(None, network, QueryType.DATA, datetime(2026, 1, 2))
    assert len(calls) == 1
    assert set(out) == {datetime(2026, 1, 1, 12, 0)}
    assert not intervals._inflight
