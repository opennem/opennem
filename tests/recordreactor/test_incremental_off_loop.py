"""The incremental milestone pass must not block the ARQ worker event loop with ClickHouse calls.

clickhouse-driver is fully synchronous; calling it from the async pass stalled the whole worker for
up to 14.5s (BACKEND-642). The queries now run on worker threads, each with its own thread-local
client so a coroutine on the loop using the loop thread's client can't collide with them.
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Any

import pytest

from opennem import settings
from opennem.recordreactor import incremental, queries_incremental
from opennem.schema.network import NetworkNEM

NOW = datetime(2026, 9, 22, 14, 0)
SETTLED = NOW - timedelta(minutes=30)


class _FakeClient:
    """Stands in for clickhouse_driver.Client; records every query in the order issued."""

    def __init__(self, sleep: float = 0.0) -> None:
        self.queries: list[str] = []
        self.threads: set[int] = set()
        self._sleep = sleep

    def execute(self, query: str, *args: Any, **kwargs: Any) -> list[tuple]:
        self.queries.append(query)
        self.threads.add(threading.get_ident())
        if self._sleep:
            time.sleep(self._sleep)
        if query.startswith("Q|"):
            return [(SETTLED, 1.0, 1)]
        return []


def _patch_pass(monkeypatch, client: _FakeClient) -> list[tuple[str, str]]:
    mapped: list[tuple[str, str]] = []
    field_names: dict[str, tuple[str, ...]] = {}

    def _build(metric_def, network, grouping, period, period_start, period_end) -> str:
        field_names[grouping.name] = tuple(grouping.group_by_fields)
        return f"Q|{metric_def.metric.value}|{period.value}|{grouping.name}"

    def _map(row, metric_def, grouping, period, network, **kwargs) -> list:
        mapped.append((f"{metric_def.metric.value}|{period.value}|{grouping.name}", repr(sorted(row))))
        return []

    async def _no_rebuild(caller: str) -> bool:
        return False

    async def _no_gap() -> None:
        return None

    async def _no_state() -> dict:
        return {}

    async def _no_settled() -> dict:
        return {}

    async def _record(when: datetime, settled_intervals: dict | None = None) -> None:
        return None

    monkeypatch.setattr(settings, "milestone_interval_settle_lag_minutes", 60)
    monkeypatch.setattr(settings, "milestone_interval_max_catchup_hours", 24)
    monkeypatch.setattr(queries_incremental, "build_period_aggregation_query", _build)
    monkeypatch.setattr(queries_incremental, "query_last_rooftop_interval", lambda **kwargs: SETTLED)
    monkeypatch.setattr(incremental, "_map_row_to_records", _map)
    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _no_rebuild)
    monkeypatch.setattr(incremental, "_enqueue_gap_backfill_if_needed", _no_gap)
    monkeypatch.setattr(incremental, "get_clickhouse_client", lambda: client)
    monkeypatch.setattr(incremental, "refresh_current_milestone_state", _no_state)
    monkeypatch.setattr(incremental, "get_last_settled_intervals", _no_settled)
    monkeypatch.setattr(incremental, "get_last_completed_interval_for_network", lambda *a, **k: NOW + timedelta(minutes=5))
    monkeypatch.setattr(incremental, "set_last_incremental_run", _record)
    return mapped


@pytest.mark.asyncio
async def test_pass_issues_the_same_queries_in_the_same_order(monkeypatch) -> None:
    client = _FakeClient()
    mapped = _patch_pass(monkeypatch, client)

    await incremental.run_incremental_milestone_check(networks=[NetworkNEM], alert_slack=False)

    assert len(client.queries) > 2
    assert all(q.startswith("Q|") for q in client.queries)
    # every query's row was mapped, in query order
    assert [m[0] for m in mapped] == [q.removeprefix("Q|") for q in client.queries]
    # the sequence is stable (no reordering or duplication from running off the loop)
    assert len(set(client.queries)) == len(client.queries)


@pytest.mark.asyncio
async def test_pass_does_not_block_the_event_loop(monkeypatch) -> None:
    client = _FakeClient(sleep=0.3)
    _patch_pass(monkeypatch, client)
    # one slow query is enough to show a stall
    real = incremental.get_completed_periods
    monkeypatch.setattr(incremental, "get_completed_periods", lambda *a, **k: real(*a, **k)[:1])

    ticks: list[float] = []

    async def _ticker() -> None:
        while True:
            ticks.append(time.monotonic())
            await asyncio.sleep(0.05)

    task = asyncio.create_task(_ticker())
    await asyncio.sleep(0)
    await incremental.run_incremental_milestone_check(networks=[NetworkNEM], alert_slack=False)
    task.cancel()

    gaps = [b - a for a, b in zip(ticks, ticks[1:], strict=False)]
    assert client.queries, "no query issued"
    assert max(gaps) < 0.25, f"event loop stalled for {max(gaps):.2f}s"
    assert threading.get_ident() not in client.threads
