"""The live v4 endpoints must cap date_end at the latest settled interval so the
provisional bleeding-edge interval is never served (#575).

`cap_date_end_to_settled_interval` treats max(interval) as an exclusive upper bound
(the query uses `interval < date_end`), with safe fallbacks on empty/error/inverted
ranges.
"""

from datetime import datetime

import pytest

import opennem.api.intervals as intervals
from opennem.api.intervals import cap_date_end_to_settled_interval
from opennem.api.queries import QueryType
from opennem.schema.network import NetworkNEM


@pytest.fixture(autouse=True)
def _clear_cache():
    intervals._latest_interval_cache.clear()
    yield
    intervals._latest_interval_cache.clear()


def _fake_execute_returning(value):
    async def _fake(client, query, params):  # noqa: ANN001, ANN202
        return [[value]]

    return _fake


@pytest.mark.asyncio
async def test_caps_to_latest_when_data_lags_wall_clock(monkeypatch):
    latest = datetime(2026, 6, 22, 9, 45)
    monkeypatch.setattr(intervals, "execute_async", _fake_execute_returning(latest))

    capped = await cap_date_end_to_settled_interval(
        client=object(),
        network=NetworkNEM,
        query_type=QueryType.DATA,
        date_end=datetime(2026, 6, 22, 9, 55),  # wall-clock boundary, ahead of data
    )
    # capped to max(interval); `interval < date_end` then excludes the provisional latest
    assert capped == latest


@pytest.mark.asyncio
async def test_returns_date_end_on_error(monkeypatch):
    async def _boom(client, query, params):  # noqa: ANN001, ANN202
        raise RuntimeError("clickhouse down")

    monkeypatch.setattr(intervals, "execute_async", _boom)
    date_end = datetime(2026, 6, 22, 9, 55)

    capped = await cap_date_end_to_settled_interval(
        client=object(),
        network=NetworkNEM,
        query_type=QueryType.MARKET,
        date_end=date_end,
    )
    assert capped == date_end


@pytest.mark.asyncio
async def test_returns_date_end_on_empty_table(monkeypatch):
    monkeypatch.setattr(intervals, "execute_async", _fake_execute_returning(None))
    date_end = datetime(2026, 6, 22, 9, 55)

    capped = await cap_date_end_to_settled_interval(
        client=object(),
        network=NetworkNEM,
        query_type=QueryType.MARKET,
        date_end=date_end,
    )
    assert capped == date_end


@pytest.mark.asyncio
async def test_caps_unconditionally_even_on_bleeding_edge_window(monkeypatch):
    """A live window sitting entirely on the bleeding edge still caps at the settled
    boundary — the caller's query then yields no rows (404) rather than the known-bad
    provisional interval."""
    latest = datetime(2026, 6, 22, 9, 45)
    monkeypatch.setattr(intervals, "execute_async", _fake_execute_returning(latest))

    capped = await cap_date_end_to_settled_interval(
        client=object(),
        network=NetworkNEM,
        query_type=QueryType.DATA,
        date_end=datetime(2026, 6, 22, 9, 55),
    )
    assert capped == latest


@pytest.mark.asyncio
async def test_result_is_cached_within_ttl(monkeypatch):
    latest = datetime(2026, 6, 22, 9, 45)
    calls = {"n": 0}

    async def _counting(client, query, params):  # noqa: ANN001, ANN202
        calls["n"] += 1
        return [[latest]]

    monkeypatch.setattr(intervals, "execute_async", _counting)
    kwargs = {
        "client": object(),
        "network": NetworkNEM,
        "query_type": QueryType.DATA,
        "date_end": datetime(2026, 6, 22, 9, 55),
    }

    await cap_date_end_to_settled_interval(**kwargs)
    await cap_date_end_to_settled_interval(**kwargs)
    assert calls["n"] == 1  # second call served from the TTL cache
