"""Pollution response-body cache: hit/miss, key normalisation, errors, backend failure, versioning, byte identity."""

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI, Request, Response
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from opennem.api.pollution import cache as pollution_cache
from opennem.api.pollution import router as pollution_router
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.security import get_current_user
from opennem.api.timeseries import TimeSeries
from tests.api.test_pollution_narrow_query import _data, _Session

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(autouse=True)
async def _cache() -> Any:
    InMemoryBackend._store.clear()  # class-level dict shared across instances
    FastAPICache.init(InMemoryBackend(), prefix="test")
    yield
    FastAPICache.reset()


class _FreshSession(_Session):
    """Per-instance first execute = facilities, second = pollution rows (shared log spans several computes)."""

    def __init__(self, *a: Any) -> None:
        super().__init__(*a)
        self.n = 0

    async def execute(self, stmt: Any) -> Any:
        self.log.append(stmt)
        self.n += 1
        if self.n == 1:
            return SimpleNamespace(all=lambda: self.facilities)
        return SimpleNamespace(all=lambda: self.rows)


def _patch_db(monkeypatch: pytest.MonkeyPatch, empty: bool = False) -> list[Any]:
    log: list[Any] = []
    facs, rows = _data(empty_rows=empty)
    monkeypatch.setattr(pollution_router, "get_read_session", lambda: _FreshSession(facs, rows, log))
    return log


async def _call(**kw: Any) -> Response:
    args: dict[str, Any] = {
        "facility_code": None,
        "pollutant_code": None,
        "pollutant_category": None,
        "date_start": None,
        "date_end": None,
    }
    args.update(kw)
    return await pollution_router.get_facility_pollution(
        request=Request({"type": "http", "headers": []}),
        response=Response(),
        user=None,  # pyright: ignore[reportArgumentType]
        **args,
    )


async def test_miss_computes_and_hit_skips_db(monkeypatch: pytest.MonkeyPatch) -> None:
    log = _patch_db(monkeypatch)
    first = await _call()
    assert len(log) == 2
    second = await _call()
    assert len(log) == 2, "hit must not touch the DB"
    assert bytes(first.body) == bytes(second.body)
    assert second.status_code == 200 and second.media_type == "application/json"


async def test_key_normalisation() -> None:
    k = pollution_cache.build_cache_key
    assert k(["B", "A"], ["SO2", "NOX"], None, None) == k(["A", "B", "A"], ["NOX", "SO2"], None, None)
    assert k(None, ["NOX"], None, None) != k(["A"], ["NOX"], None, None)
    from datetime import datetime

    assert k(None, ["NOX"], datetime(2019, 1, 1), None) == k(None, ["NOX"], datetime(2019, 12, 31), None)
    assert k(None, ["NOX"], datetime(2019, 1, 1), None) != k(None, ["NOX"], datetime(2020, 1, 1), None)


async def test_param_order_shares_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.schema.pollution import PollutantCode

    log = _patch_db(monkeypatch)
    await _call(facility_code=["F1", "F2"], pollutant_code=[PollutantCode.NOX, PollutantCode.SO2])
    n = len(log)
    await _call(facility_code=["F2", "F1"], pollutant_code=[PollutantCode.SO2, PollutantCode.NOX])
    assert len(log) == n


async def test_errors_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi import HTTPException

    _patch_db(monkeypatch, empty=True)
    with pytest.raises(HTTPException) as e:
        await _call()
    assert e.value.status_code == 404
    log = _patch_db(monkeypatch)  # data appears: must compute, not replay the 404
    resp = await _call()
    assert resp.status_code == 200 and len(log) == 2


async def test_backend_failure_falls_back_to_compute(monkeypatch: pytest.MonkeyPatch) -> None:
    log = _patch_db(monkeypatch)
    expected = bytes((await _call()).body)

    class _Broken(InMemoryBackend):
        async def get(self, key: str) -> Any:
            raise ConnectionError("redis down")

        async def set(self, key: str, value: bytes, expire: int | None = None) -> None:
            raise ConnectionError("redis down")

    FastAPICache.reset()
    FastAPICache.init(_Broken(), prefix="test")
    monkeypatch.setattr(pollution_cache, "_last_warn", 0.0)
    before = len(log)
    resp = await _call()
    assert bytes(resp.body) == expected and len(log) == before + 2


async def test_version_bump_invalidates(monkeypatch: pytest.MonkeyPatch) -> None:
    log = _patch_db(monkeypatch)
    await _call()
    await _call()
    assert len(log) == 2
    await pollution_cache.bump_pollution_version()
    await _call()
    assert len(log) == 4


async def test_user_does_not_fragment_key(monkeypatch: pytest.MonkeyPatch) -> None:
    log = _patch_db(monkeypatch)
    app = FastAPI()
    app.include_router(pollution_router.router, prefix="/pollution")
    users = iter(["a", "b"])
    app.dependency_overrides[get_current_user] = lambda: next(users)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r1 = await c.get("/pollution/facilities")
        r2 = await c.get("/pollution/facilities")
    assert r1.status_code == r2.status_code == 200 and r1.content == r2.content
    assert len(log) == 2


async def test_bytes_identical_to_plain_response_model_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cached body (miss and hit) equals what FastAPI emits when the handler returns the model."""
    _patch_db(monkeypatch)
    app = FastAPI()
    app.include_router(pollution_router.router, prefix="/pollution")
    app.dependency_overrides[get_current_user] = lambda: None

    async def plain() -> APIV4ResponseSchema[list[TimeSeries]]:
        return await pollution_router._build_response(None, pollution_router._resolve_pollutant_codes(None, None), None, None)

    app.add_api_route(
        "/plain",
        plain,
        response_model=APIV4ResponseSchema[list[TimeSeries]],
        response_model_exclude_none=True,
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        miss = await c.get("/pollution/facilities")
        hit = await c.get("/pollution/facilities")
        ref = await c.get("/plain")
    # created_at is stamped per construction; compare everything else
    import json

    def norm(b: bytes) -> dict[str, Any]:
        d = json.loads(b)
        d.pop("created_at", None)
        return d

    assert miss.content == hit.content
    assert norm(miss.content) == norm(ref.content)
    assert miss.headers["content-type"] == ref.headers["content-type"] == "application/json"
