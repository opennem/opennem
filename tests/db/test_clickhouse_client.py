"""Tests for the ClickHouse serving-path query settings applied by execute_async."""

import asyncio
import threading
import time

import pytest

from opennem import settings
from opennem.db.clickhouse import client as ch_client


class _FakeClient:
    """Records the args of the last execute() call."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def execute(self, query, params=None, **kwargs):  # noqa: ANN001, ANN003
        self.calls.append({"query": query, "params": params, "kwargs": kwargs})
        return []


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> _FakeClient:
    fake = _FakeClient()
    monkeypatch.setattr(ch_client, "get_clickhouse_client", lambda *a, **k: fake)
    return fake


@pytest.mark.asyncio
async def test_execute_async_applies_default_memory_limits(fake_client: _FakeClient) -> None:
    await ch_client.execute_async(fake_client, "SELECT 1")

    applied = fake_client.calls[-1]["kwargs"]["settings"]
    assert applied["max_memory_usage"] == settings.clickhouse_query_max_memory_usage
    assert applied["max_bytes_before_external_group_by"] == settings.clickhouse_query_max_bytes_before_external_group_by
    assert applied["max_execution_time"] == settings.clickhouse_query_max_execution_time


@pytest.mark.asyncio
async def test_caller_settings_override_per_key(fake_client: _FakeClient) -> None:
    await ch_client.execute_async(fake_client, "SELECT 1", settings={"max_memory_usage": 123, "readonly": 1})

    applied = fake_client.calls[-1]["kwargs"]["settings"]
    # caller wins per-key
    assert applied["max_memory_usage"] == 123
    # caller-only keys are merged in
    assert applied["readonly"] == 1
    # untouched defaults remain
    assert applied["max_execution_time"] == settings.clickhouse_query_max_execution_time


@pytest.mark.asyncio
async def test_limits_can_be_disabled(fake_client: _FakeClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "clickhouse_query_max_memory_usage", 0)
    monkeypatch.setattr(settings, "clickhouse_query_max_bytes_before_external_group_by", 0)
    monkeypatch.setattr(settings, "clickhouse_query_max_execution_time", 0)

    await ch_client.execute_async(fake_client, "SELECT 1")

    assert fake_client.calls[-1]["kwargs"]["settings"] == {}


@pytest.mark.asyncio
async def test_insert_async_passes_data_without_serving_settings(fake_client: _FakeClient) -> None:
    """Write path must forward the row data and NOT apply serving-path resource limits."""
    rows = [(1, "a"), (2, "b")]

    await ch_client.insert_async("INSERT INTO t VALUES", rows)

    call = fake_client.calls[-1]
    assert call["params"] == rows
    # no settings kwarg (serving limits) on the write path
    assert "settings" not in call["kwargs"]


@pytest.mark.asyncio
async def test_insert_async_runs_off_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """The blocking driver call must run in a worker thread so the loop stays responsive.

    Regression guard for #572: blocking the event loop starves asyncpg connections that
    are checked out from the pool and leaks them.
    """
    loop_thread = threading.get_ident()
    exec_thread: list[int] = []

    class _BlockingClient:
        def execute(self, query, data=None, **kwargs):  # noqa: ANN001, ANN003
            exec_thread.append(threading.get_ident())
            time.sleep(0.2)
            return []

    monkeypatch.setattr(ch_client, "get_clickhouse_client", lambda *a, **k: _BlockingClient())

    ticks = 0

    async def _ticker() -> None:
        nonlocal ticks
        for _ in range(10):
            await asyncio.sleep(0.02)
            ticks += 1

    await asyncio.gather(ch_client.insert_async("INSERT INTO t VALUES", [(1,)]), _ticker())

    # the concurrent coroutine kept running during the 0.2s blocking insert
    assert ticks == 10
    # and the blocking call did not run on the event loop thread
    assert exec_thread and exec_thread[0] != loop_thread
