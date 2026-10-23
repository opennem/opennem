"""#751: keyed responses are `private` + `Vary: Authorization` (miss and hit); anonymous stay public; errors uncached."""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Annotated, Any

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from httpx import ASGITransport, AsyncClient

from opennem.api import response_cache as rc
from opennem.api.cache_keys import tiered_key_builder
from opennem.api.response_cache import apply_cache_visibility, cached_json, private_when_keyed
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit

pytestmark = pytest.mark.asyncio

KEYED = {"Authorization": "Bearer k"}


def _user() -> OpenNEMUser:
    return OpenNEMUser(
        id="u",
        plan=OpenNEMPlan.COMMUNITY,
        roles=[OpenNEMRoles.anonymous],
        rate_limit=OpenNEMUserRateLimit(limit=60, remaining=5, reset=1_700_000_000_000),
    )


async def _optional_user(authorization: Annotated[str | None, Header()] = None) -> OpenNEMUser | None:
    return _user() if authorization else None


async def _required_user(authorization: Annotated[str | None, Header()] = None) -> OpenNEMUser:
    if authorization is None:
        raise HTTPException(status_code=401, detail="no key")
    return _user()


def _make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/opt")
    @cached_json(expire=300, live_expire=60, key_builder=tiered_key_builder, return_type=None)
    async def opt(
        user: Annotated[OpenNEMUser | None, Depends(_optional_user)],
        date_start: datetime | None = None,
        date_end: datetime | None = None,
    ) -> dict[str, int]:
        return {"ok": 1}

    @app.get("/req")
    @cached_json(expire=300, key_builder=tiered_key_builder, return_type=None)
    async def req(user: Annotated[OpenNEMUser, Depends(_required_user)]) -> dict[str, int]:
        return {"ok": 1}

    @app.get("/nf")
    @cached_json(expire=300, key_builder=tiered_key_builder, return_type=None)
    async def nf(user: Annotated[OpenNEMUser | None, Depends(_optional_user)]) -> dict[str, int]:
        raise HTTPException(status_code=404, detail="nope")

    @app.get("/plain")
    @private_when_keyed
    @cache(expire=300, key_builder=tiered_key_builder)
    async def plain(user: Annotated[OpenNEMUser | None, Depends(_optional_user)]) -> dict[str, int]:
        return {"ok": 1}

    return app


@pytest_asyncio.fixture(autouse=True)
async def _cache() -> AsyncIterator[None]:
    InMemoryBackend._store.clear()
    FastAPICache.init(InMemoryBackend(), prefix="test")
    yield
    FastAPICache.reset()


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=_make_app()), base_url="http://t")


def _max_age(cc: str) -> int:
    return int(next(d.split("=")[1] for d in cc.split(", ") if d.startswith("max-age=")))


@pytest.mark.parametrize("path", ["/req", "/opt?date_end=2020-01-01T00:00:00"])
async def test_keyed_miss_and_hit_are_private(path: str) -> None:
    async with _client() as c:
        miss = await c.get(path, headers=KEYED)
        hit = await c.get(path, headers=KEYED)
    assert miss.headers["x-fastapi-cache"] == "MISS" and hit.headers["x-fastapi-cache"] == "HIT"
    for r in (miss, hit):
        assert r.status_code == 200
        assert r.headers["cache-control"].startswith("private, max-age=")
        assert r.headers["vary"] == "Authorization"
    assert _max_age(miss.headers["cache-control"]) == 300
    assert _max_age(hit.headers["cache-control"]) <= 300


async def test_anonymous_miss_and_hit_stay_public() -> None:
    async with _client() as c:
        miss = await c.get("/opt?date_end=2020-01-01T00:00:00")
        hit = await c.get("/opt?date_end=2020-01-01T00:00:00")
    for r in (miss, hit):
        assert r.headers["cache-control"].startswith("max-age=")
        assert "private" not in r.headers["cache-control"]
        assert "vary" not in r.headers


async def test_keyed_then_anonymous_same_url() -> None:
    """the leak: a keyed fill then an anonymous read of the same URL; each gets its own directive"""
    async with _client() as c:
        keyed = await c.get("/opt", headers=KEYED)
        anon = await c.get("/opt")
    assert keyed.headers["cache-control"] == "private, max-age=60"
    assert anon.headers["cache-control"] == "max-age=60"


async def test_live_ttl_preserved() -> None:
    async with _client() as c:
        live = await c.get("/opt", headers=KEYED)
        hist = await c.get("/opt?date_end=2020-01-01T00:00:00", headers=KEYED)
    assert live.headers["cache-control"] == "private, max-age=60"
    assert hist.headers["cache-control"] == "private, max-age=300"


async def test_slot_ttl_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rc, "grid_slot_end", lambda kwargs: datetime(2026, 1, 1))
    monkeypatch.setattr(rc, "slot_live_ttl", lambda slot_end, floor, now=None: 240)
    async with _client() as c:
        miss = await c.get("/opt", headers=KEYED)
        hit = await c.get("/opt", headers=KEYED)
    assert miss.headers["cache-control"] == "private, max-age=240"
    assert hit.headers["cache-control"].startswith("private, max-age=")
    assert _max_age(hit.headers["cache-control"]) <= 240


async def test_errors_have_no_cache_control() -> None:
    async with _client() as c:
        unauth = await c.get("/req")
        notfound = await c.get("/nf", headers=KEYED)
        notfound_anon = await c.get("/nf")
    assert unauth.status_code == 401
    assert notfound.status_code == notfound_anon.status_code == 404
    for r in (unauth, notfound, notfound_anon):
        assert "max-age" not in r.headers.get("cache-control", "")


async def test_plain_cache_decorator_private_when_keyed() -> None:
    async with _client() as c:
        keyed_miss = await c.get("/plain", headers=KEYED)
        keyed_hit = await c.get("/plain", headers=KEYED)
        anon = await c.get("/plain")
    assert keyed_miss.headers["cache-control"] == "private, max-age=300"
    assert keyed_hit.headers["cache-control"].startswith("private, max-age=")
    assert keyed_hit.headers["vary"] == "Authorization"
    assert anon.headers["cache-control"].startswith("max-age=") and "private" not in anon.headers["cache-control"]


@pytest.mark.parametrize(
    ("headers", "authorized", "cc", "vary"),
    [
        ({"cache-control": "max-age=60"}, True, "private, max-age=60", "Authorization"),
        ({"cache-control": "max-age=60", "vary": "Accept"}, True, "private, max-age=60", "Accept, Authorization"),
        ({"cache-control": "private, max-age=60", "vary": "authorization"}, True, "private, max-age=60", "authorization"),
        ({"cache-control": "max-age=60"}, False, "max-age=60", None),
        ({}, True, None, None),
        ({"cache-control": "no-store"}, True, "no-store", None),
    ],
)
def test_apply_cache_visibility(headers: dict[str, str], authorized: bool, cc: str | None, vary: str | None) -> None:
    h: dict[str, Any] = dict(headers)
    apply_cache_visibility(h, authorized)
    assert h.get("Cache-Control", h.get("cache-control")) == cc
    assert h.get("Vary", h.get("vary")) == vary
