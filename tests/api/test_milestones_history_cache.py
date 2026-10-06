"""Caching on GET /milestones/history/{record_id} (#648).

Pins: one cache entry per (record_id, page, limit), hits byte-identical to misses, error envelopes
never cached, private (browser-only) cache-control, and auth dependencies still running on hits.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable, Iterator
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from opennem.api.milestones import router as milestones_module
from opennem.api.milestones.router import (
    MILESTONE_HISTORY_CACHE_TTL,
    _milestone_history_cache_key,
    milestones_router,
)
from opennem.api.security import get_current_user
from opennem.db import get_scoped_read_session

RECORD_ID = "au.nem.wind.power.interval.high"


def _db_row(record_id: str = RECORD_ID) -> dict:
    return {
        "instance_id": uuid.UUID("01a0cbb6-e2cc-7852-8960-38e78197e4ca"),
        "record_id": record_id,
        "interval": datetime(2026, 7, 1, 21, 20),
        "aggregate": "high",
        "period": "interval",
        "metric": "power",
        "network_id": "NEM",
        "network_region": None,
        "fueltech_id": "wind",
        "significance": 10,
        "value": 10349.0,
        "pct_change": 0.38,
        "value_unit": "MW",
        "description": "Interval Wind Generation high record for NEM",
        "previous_instance_id": None,
    }


async def _fake_db() -> AsyncGenerator[None]:
    yield None


async def _any_caller() -> None:
    return None


def _make_client(auth: Callable[..., Awaitable[None]] = _any_caller) -> TestClient:
    """The router requires `get_current_user`; tests stand it in rather than hitting unkey"""
    app = FastAPI()
    app.include_router(milestones_router)
    app.dependency_overrides[get_scoped_read_session] = _fake_db
    app.dependency_overrides[get_current_user] = auth
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def api_cache() -> Iterator[None]:
    FastAPICache.reset()
    # InMemoryBackend shares one class-level store, so isolate each test with its own prefix
    prefix = f"test-{uuid.uuid4().hex}"
    backend = InMemoryBackend()
    FastAPICache.init(backend, prefix=prefix)
    yield
    asyncio.run(backend.clear(namespace=prefix))
    FastAPICache.reset()


@pytest.fixture
def query() -> Iterator[AsyncMock]:
    mock = AsyncMock(return_value=([_db_row()], 1))
    with patch.object(milestones_module, "get_milestone_records", mock):
        yield mock


def test_second_request_is_a_cache_hit_with_identical_body(query: AsyncMock) -> None:
    client = _make_client()

    miss = client.get(f"/history/{RECORD_ID}?limit=1")
    hit = client.get(f"/history/{RECORD_ID}?limit=1")

    assert miss.status_code == hit.status_code == 200
    assert miss.headers["x-fastapi-cache"] == "MISS"
    assert hit.headers["x-fastapi-cache"] == "HIT"
    assert hit.content == miss.content
    assert miss.json()["data"][0]["record_id"] == RECORD_ID
    # None fields stay excluded on hits too (response_model_exclude_none)
    assert "network_region" not in hit.json()["data"][0]
    assert query.await_count == 1


def test_cache_control_is_private_never_shared(query: AsyncMock) -> None:
    client = _make_client()

    for response in (client.get(f"/history/{RECORD_ID}"), client.get(f"/history/{RECORD_ID}")):
        cache_control = response.headers["cache-control"]
        assert cache_control.startswith("private, max-age=")
        assert "public" not in cache_control
        assert "s-maxage" not in cache_control
        assert 0 <= int(cache_control.rsplit("=", 1)[1]) <= MILESTONE_HISTORY_CACHE_TTL


def test_cache_key_includes_record_id_page_and_limit(query: AsyncMock) -> None:
    client = _make_client()

    paths = [
        f"/history/{RECORD_ID}",
        f"/history/{RECORD_ID}?page=2",
        f"/history/{RECORD_ID}?limit=5",
        f"/history/{RECORD_ID}?limit=5&page=2",
        "/history/au.nem.solar.power.interval.high",
    ]

    for path in paths:
        assert client.get(path).headers["x-fastapi-cache"] == "MISS", path

    assert query.await_count == len(paths)
    seen = {(c.kwargs["record_id"], c.kwargs["page_number"], c.kwargs["limit"]) for c in query.await_args_list}
    assert seen == {
        (RECORD_ID, 1, 1000),
        (RECORD_ID, 2, 1000),
        (RECORD_ID, 1, 5),
        (RECORD_ID, 2, 5),
        ("au.nem.solar.power.interval.high", 1, 1000),
    }

    for path in paths:
        assert client.get(path).headers["x-fastapi-cache"] == "HIT", path
    assert query.await_count == len(paths)


def test_unlimited_requests_share_one_entry_across_pages(query: AsyncMock) -> None:
    """limit=0 skips LIMIT/OFFSET so page is ignored by the query, and must not multiply cache entries"""
    client = _make_client()

    assert client.get(f"/history/{RECORD_ID}?limit=0&page=1").headers["x-fastapi-cache"] == "MISS"
    assert client.get(f"/history/{RECORD_ID}?limit=0&page=7").headers["x-fastapi-cache"] == "HIT"
    assert query.await_count == 1


def test_cache_key_is_unambiguous() -> None:
    keys = {
        _milestone_history_cache_key("a", 1, 10),
        _milestone_history_cache_key("a", 2, 10),
        _milestone_history_cache_key("a", 1, 20),
        _milestone_history_cache_key("b", 1, 10),
        _milestone_history_cache_key("a:1", 10, 1),
    }
    assert len(keys) == 5


def test_error_responses_are_not_cached(query: AsyncMock) -> None:
    client = _make_client()
    query.side_effect = [RuntimeError("db down"), ([_db_row()], 1)]

    failed = client.get(f"/history/{RECORD_ID}")
    assert failed.json()["success"] is False
    assert "x-fastapi-cache" not in failed.headers

    recovered = client.get(f"/history/{RECORD_ID}")
    assert recovered.json()["success"] is True
    assert recovered.headers["x-fastapi-cache"] == "MISS"
    assert query.await_count == 2


def test_not_found_is_not_cached(query: AsyncMock) -> None:
    """The route is unauthenticated, so caching misses would let arbitrary record ids fill the cache"""
    client = _make_client()
    query.return_value = ([], 0)

    for _ in range(2):
        response = client.get("/history/au.nem.not.a.record")
        assert response.json()["error"] == "Milestone record not found"
        assert response.headers["x-fastapi-cache"] == "MISS"

    assert query.await_count == 2


def test_negative_limit_is_rejected(query: AsyncMock) -> None:
    client = _make_client()

    assert client.get(f"/history/{RECORD_ID}?limit=-5").status_code == 400
    assert query.await_count == 0


def test_auth_dependency_runs_on_cache_hits(query: AsyncMock) -> None:
    """The router auth dependency runs before the endpoint, hit or miss.
    The cache key ignores the caller, so callers share entries but each one is still checked."""
    seen_tokens: list[str | None] = []

    async def fake_auth(request: Request) -> None:
        token = request.headers.get("authorization")
        seen_tokens.append(token)
        if token not in ("Bearer key-a", "Bearer key-b"):
            raise HTTPException(status_code=401, detail="Invalid API key")

    client = _make_client(fake_auth)

    first = client.get(f"/history/{RECORD_ID}", headers={"Authorization": "Bearer key-a"})
    second = client.get(f"/history/{RECORD_ID}", headers={"Authorization": "Bearer key-b"})
    anonymous = client.get(f"/history/{RECORD_ID}")

    assert first.headers["x-fastapi-cache"] == "MISS"
    assert second.headers["x-fastapi-cache"] == "HIT"
    assert anonymous.status_code == 401
    assert seen_tokens == ["Bearer key-a", "Bearer key-b", None]
    assert query.await_count == 1


def test_works_without_cache_initialised(query: AsyncMock) -> None:
    FastAPICache.reset()
    client = _make_client()

    for _ in range(2):
        response = client.get(f"/history/{RECORD_ID}")
        assert response.status_code == 200
        assert response.headers["x-fastapi-cache"] == "MISS"

    assert query.await_count == 2
