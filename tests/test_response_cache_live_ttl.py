"""cached_json uses a short TTL for live-edge requests and keeps the long TTL for old ranges (#726)."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from opennem.api.cache_keys import tiered_key_builder
from opennem.api.response_cache import cached_json, is_live_edge_request

NOW = datetime(2026, 10, 12, 19, 0, tzinfo=timezone(timedelta(hours=10)))


@pytest.mark.parametrize(
    ("date_end", "live"),
    [
        (None, True),
        (datetime(2026, 10, 12, 18, 55), True),
        (datetime(2026, 10, 13, 0, 0), True),  # future (forecast)
        (datetime(2026, 10, 11, 19, 30), True),  # within the last day
        (datetime(2026, 10, 11, 18, 0), False),
        (datetime(2025, 1, 1), False),
        (datetime(2026, 10, 12, 8, 55, tzinfo=UTC), True),  # aware input, 18:55 NEM
    ],
)
def test_is_live_edge_request(date_end: datetime | None, live: bool) -> None:
    assert is_live_edge_request(date_end, now=NOW) is live


@pytest_asyncio.fixture
async def init_cache():
    FastAPICache.init(InMemoryBackend(), prefix="t")
    yield
    FastAPICache.reset()


async def _max_ages(date_end: datetime | None) -> tuple[int, int]:
    """(MISS max-age, HIT max-age) as the client sees them for a direct handler call."""
    from fastapi import Response

    calls = {"n": 0}

    @cached_json(expire=300, live_expire=60, key_builder=tiered_key_builder)
    async def handler(date_end: datetime | None = None, user=None, client=None) -> dict:
        calls["n"] += 1
        return {"ok": True}

    ages = []
    for _ in range(2):
        out = await handler(date_end=date_end, user=None, client=None, __fastapi_cache_response=Response())
        ages.append(int(out.headers["cache-control"].split("max-age=")[1]))
    assert calls["n"] == 1  # second call was a HIT
    return ages[0], ages[1]


@pytest.mark.asyncio
async def test_live_edge_uses_60s_and_matching_max_age(init_cache) -> None:
    miss, hit = await _max_ages(None)
    assert miss == 60
    assert 0 < hit <= 60


@pytest.mark.asyncio
async def test_historical_range_keeps_300s(init_cache) -> None:
    miss, hit = await _max_ages(datetime(2025, 1, 1))
    assert miss == 300
    assert 60 < hit <= 300
