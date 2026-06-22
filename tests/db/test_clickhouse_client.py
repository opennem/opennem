"""Tests for the ClickHouse serving-path query settings applied by execute_async."""

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
