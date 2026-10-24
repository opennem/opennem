"""Worker-side tracker cache warmer (#759): entries built in-process equal what a real API request builds."""

import socket
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from pydantic import SecretStr

from opennem.api.data import router as data_router
from opennem.api.market import router as market_router
from opennem.api.security import get_optional_user
from opennem.db.clickhouse import get_clickhouse_dependency
from opennem.tasks import cache_warmer as cw
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

pytestmark = pytest.mark.asyncio

SLOT_END = datetime(2026, 10, 24, 6, 20)
PLAN = OpenNEMPlan.PRO


def _user() -> OpenNEMUser:
    return OpenNEMUser(id="fe", plan=PLAN, roles=[OpenNEMRoles.anonymous])


def _fresh_backend() -> InMemoryBackend:
    backend = InMemoryBackend()
    backend._store.clear()  # pyright: ignore[reportAttributeAccessIssue]  # the store is class-level (shared)
    FastAPICache.init(backend, prefix="api-cache")
    return backend


@pytest_asyncio.fixture(autouse=True)
async def _cache() -> AsyncIterator[None]:
    _fresh_backend()
    yield
    FastAPICache.reset()


@pytest.fixture
def stubs(monkeypatch: pytest.MonkeyPatch) -> dict[str, MagicMock]:
    """Stub the query layer of both routes; counters show how many real builds ran."""
    execute = AsyncMock(return_value=[("x",)])
    monkeypatch.setattr(data_router, "validate_date_range", lambda **kw: (kw["date_start"], kw["date_end"]))
    monkeypatch.setattr(data_router, "get_timeseries_query", lambda **kw: ("q", {}, ["c"]))
    monkeypatch.setattr(data_router, "execute_async", execute)
    monkeypatch.setattr(
        data_router, "rows_to_timeseries_response", lambda *a, **kw: {"data": [{"v": "é", "n": len(execute.mock_calls)}]}
    )
    monkeypatch.setattr(data_router, "columnar_to_timeseries_response", lambda *a, **kw: {"data": [{"v": "é", "n": 0}]})
    actual = AsyncMock(return_value=([{"metric": "price", "d": datetime(2026, 1, 1)}], True))
    monkeypatch.setattr(market_router, "_actual_timeseries", actual)
    monkeypatch.setattr(market_router, "build_timeseries_response", lambda ts: {"data": ts})
    return {"data": execute, "market": actual}


def _req(kind: str, metrics: tuple[str, ...], region: str | None = "NSW1", span: timedelta = timedelta(days=1)) -> cw.WarmRequest:
    return cw._request(kind, metrics, region, SLOT_END - span, SLOT_END, "5m")


def _http_app() -> FastAPI:
    app = FastAPI()
    app.include_router(data_router.router, prefix="/v4/data")
    app.include_router(market_router.router, prefix="/v4/market")
    app.dependency_overrides[get_optional_user] = lambda: _user()

    async def _no_client() -> AsyncIterator[object]:
        yield object()

    app.dependency_overrides[get_clickhouse_dependency] = _no_client
    return app


async def _real_http(req: cw.WarmRequest, *, no_cache: bool = False) -> httpx.Response:
    headers = {"Authorization": "Bearer x" * 4}
    if no_cache:
        headers["Cache-Control"] = "no-cache"
    transport = httpx.ASGITransport(app=_http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        return await c.get(req.path.replace("/v4/", "/v4/", 1), params=list(req.params), headers=headers)


def _cases() -> list[cw.WarmRequest]:
    return [
        _req("data", ("power",)),
        _req("data", ("emissions", "power"), None, timedelta(days=3)),
        _req("market", ("price",)),
        _req("market", ("flow_imports", "flow_exports"), "VIC1"),
    ]


@pytest.mark.parametrize("idx", range(4))
async def test_worker_entry_equals_real_request_entry(idx: int, stubs: dict[str, MagicMock]) -> None:
    req = _cases()[idx]
    # worker build, then clear and let a real request build into the empty store
    backend_a = _fresh_backend()
    resp = await cw.call_handler(req, client=object(), user=_user())
    assert resp.status_code == 200
    assert resp.headers[cw.CACHE_STATUS_HEADER] == "MISS"
    store_a = dict(backend_a._store)  # pyright: ignore[reportAttributeAccessIssue]
    assert len(store_a) == 1

    # real request (full FastAPI stack) into a fresh backend B: same key, same bytes
    backend_b = _fresh_backend()
    assert not backend_b._store  # pyright: ignore[reportAttributeAccessIssue]
    http = await _real_http(req)
    assert http.status_code == 200
    store_b = dict(backend_b._store)  # pyright: ignore[reportAttributeAccessIssue]
    assert list(store_a) == list(store_b), "key must be identical"
    (va,), (vb,) = store_a.values(), store_b.values()
    assert va.data == vb.data, "stored bytes must be identical"
    assert http.content == va.data


async def test_real_request_hits_worker_entry(stubs: dict[str, MagicMock]) -> None:
    req = _req("data", ("power",))
    await cw.call_handler(req, client=object(), user=_user())
    assert stubs["data"].call_count == 1
    http = await _real_http(req)
    assert http.headers[cw.CACHE_STATUS_HEADER] == "HIT"
    assert stubs["data"].call_count == 1


async def test_worker_call_forces_refresh(stubs: dict[str, MagicMock]) -> None:
    req = _req("data", ("power",))
    for n in (1, 2, 3):
        resp = await cw.call_handler(req, client=object(), user=_user())
        assert resp.headers[cw.CACHE_STATUS_HEADER] == "MISS"
        assert stubs["data"].call_count == n  # rebuilt every time despite the entry existing
    # a normal request in between is served from the entry without a build
    assert (await _real_http(req)).headers[cw.CACHE_STATUS_HEADER] == "HIT"
    assert stubs["data"].call_count == 3


async def test_other_tier_does_not_share_entry(stubs: dict[str, MagicMock]) -> None:
    req = _req("market", ("price",))
    await cw.call_handler(req, client=object(), user=_user())
    other = OpenNEMUser(id="x", plan=OpenNEMPlan.COMMUNITY, roles=[OpenNEMRoles.anonymous])
    await cw.call_handler(req, client=object(), user=other)
    assert stubs["market"].call_count == 2


async def test_build_kwargs_unknown_param_rejected() -> None:
    bad = cw.WarmRequest(path="/v4/data/network/NEM", params=(("metrics", "power"), ("nope", "1")))
    with pytest.raises(ValueError, match="unknown query params"):
        cw.build_handler_kwargs(data_router.get_network_data, bad, client=None, user=None)


# --- settings gating ---


def test_enabled_gating(monkeypatch: pytest.MonkeyPatch) -> None:
    s = cw.settings
    monkeypatch.setattr(s, "cache_warm_api_url", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_api_key", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_user_plan", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_mode", "worker", raising=False)
    assert not cw.is_enabled()
    monkeypatch.setattr(s, "cache_warm_user_plan", "PRO", raising=False)
    assert cw.is_enabled()  # worker mode needs no api url
    monkeypatch.setattr(s, "cache_warm_user_plan", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_api_key", SecretStr("k"), raising=False)
    assert cw.is_enabled()
    # http mode (default) still needs url + key, and ignores the plan setting
    monkeypatch.setattr(s, "cache_warm_mode", "http", raising=False)
    assert not cw.is_enabled()
    monkeypatch.setattr(s, "cache_warm_api_url", "http://api.test", raising=False)
    assert cw.is_enabled()
    monkeypatch.setattr(s, "cache_warm_api_key", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_user_plan", "PRO", raising=False)
    assert not cw.is_enabled()


def test_default_mode_is_http() -> None:
    from opennem.settings_schema import OpennemSettings

    assert OpennemSettings.model_fields["cache_warm_mode"].default == "http"


# --- full cycle in worker mode: no network, real keys ---


async def test_worker_cycle_runs_without_network(monkeypatch: pytest.MonkeyPatch, stubs: dict[str, MagicMock]) -> None:
    s = cw.settings
    monkeypatch.setattr(s, "cache_warm_mode", "worker", raising=False)
    monkeypatch.setattr(s, "cache_warm_user_plan", PLAN.value, raising=False)
    monkeypatch.setattr(s, "cache_warm_user_admin", False, raising=False)
    monkeypatch.setattr(s, "cache_warm_api_url", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_api_key", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_concurrency", 2, raising=False)
    monkeypatch.setattr(s, "cache_warm_budget_seconds", 60, raising=False)
    monkeypatch.setattr(s, "cache_warm_include_30d", False, raising=False)
    monkeypatch.setattr(s, "cache_warm_ahead", True, raising=False)
    monkeypatch.setattr(cw, "_running", False)

    def _boom(*a: Any, **kw: Any) -> Any:
        raise AssertionError("network used in worker mode")

    with monkeypatch.context() as m:  # scoped: the real-request check below uses an in-memory httpx transport
        m.setattr(socket.socket, "connect", _boom)
        m.setattr(httpx.AsyncClient, "__init__", _boom)
        stats = await cw.run_cache_warm(now=datetime(2026, 10, 24, 6, 17, 30))
    assert stats is not None
    assert stats.errors == 0
    assert stats.ok == stats.attempted == stats.total == 2 * len(cw.build_requests(SLOT_END))
    assert stats.hit == 0
    backend = FastAPICache.get_backend()
    assert len(backend._store) == stats.total  # pyright: ignore[reportAttributeAccessIssue]  # all distinct keys
    # the real API request for a warmed slot hits
    req = _req("data", ("power",), None)
    assert (await _real_http(req)).headers[cw.CACHE_STATUS_HEADER] == "HIT"


async def test_worker_cycle_counts_handler_errors(monkeypatch: pytest.MonkeyPatch, stubs: dict[str, MagicMock]) -> None:
    stubs["market"].side_effect = RuntimeError("boom")
    stats = await cw.warm_requests(
        [_req("market", ("price",)), _req("data", ("power",))],
        None,
        concurrency=1,
        budget_seconds=30,
        warm_one=cw.make_worker_warm_one(client=object(), user=_user()),
    )
    assert (stats.attempted, stats.ok, stats.errors) == (2, 1, 1)


async def test_cycle_skipped_when_user_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    s = cw.settings
    monkeypatch.setattr(s, "cache_warm_mode", "worker", raising=False)
    monkeypatch.setattr(s, "cache_warm_user_plan", None, raising=False)
    monkeypatch.setattr(s, "cache_warm_api_key", SecretStr("secret-key-value"), raising=False)
    monkeypatch.setattr(cw, "_running", False)
    monkeypatch.setattr(cw, "resolve_warm_user", AsyncMock(side_effect=RuntimeError("secret-key-value")))
    assert await cw.run_cache_warm() is None
    assert cw._running is False


# --- startup flush keeps the api cache ---


class _FakeRedis:
    def __init__(self, keys: list[bytes]) -> None:
        self.keys = set(keys)

    async def scan_iter(self, count: int = 10) -> AsyncIterator[bytes]:
        for k in list(self.keys):
            yield k

    async def unlink(self, *keys: bytes) -> int:
        self.keys -= set(keys)
        return len(keys)


async def test_flush_keeps_api_cache_prefix() -> None:
    r = _FakeRedis([b"api-cache::rawjson-v2:abc", b"api-cache:pollution:v", b"arq:queue:x", b"arq:job:1", b"other"])
    deleted = await cw.flush_non_api_cache(r)
    assert deleted == 3
    assert r.keys == {b"api-cache::rawjson-v2:abc", b"api-cache:pollution:v"}
