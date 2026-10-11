"""cached_json: HIT returns the exact bytes the MISS path serialised, with cache headers, no re-encode."""

from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from opennem.api.cache_keys import tiered_key_builder
from opennem.api.response_cache import cached_json

pytestmark = pytest.mark.asyncio

CALLS: list[int] = []


class Item(BaseModel):
    name: str
    when: datetime
    opt: str | None = None
    renamed: int = Field(default=1, alias="Renamed")


def _make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/d")
    @cached_json(expire=60, key_builder=tiered_key_builder, return_type=None)
    async def get_d(x: int = 1) -> dict:
        CALLS.append(x)
        return {"x": x, "t": datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC), "none": None}

    @app.get("/m", response_model=Item, response_model_exclude_none=True)
    @cached_json(expire=60, key_builder=tiered_key_builder, return_type=Item, exclude_none=True)
    async def get_m() -> Item:
        return Item(name="a", when=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC), Renamed=7)

    return app


@pytest_asyncio.fixture
async def client():
    InMemoryBackend._store.clear()  # pyright: ignore[reportPrivateUsage]
    FastAPICache.reset()
    FastAPICache.init(InMemoryBackend())
    CALLS.clear()
    async with AsyncClient(transport=ASGITransport(app=_make_app()), base_url="http://t") as c:
        yield c
    FastAPICache.reset()


async def test_hit_body_identical_to_miss(client: AsyncClient) -> None:
    miss = await client.get("/d?x=2")
    hit = await client.get("/d?x=2")

    assert miss.headers["x-fastapi-cache"] == "MISS"
    assert hit.headers["x-fastapi-cache"] == "HIT"
    assert hit.content == miss.content
    assert hit.headers["content-type"] == "application/json"
    assert hit.headers["cache-control"].startswith("max-age=")
    assert "etag" in hit.headers
    assert CALLS == [2]


async def test_distinct_params_not_shared(client: AsyncClient) -> None:
    a = await client.get("/d?x=1")
    b = await client.get("/d?x=3")

    assert a.json()["x"] == 1
    assert b.json()["x"] == 3
    assert CALLS == [1, 3]


async def test_etag_304(client: AsyncClient) -> None:
    await client.get("/d")
    hit = await client.get("/d")
    again = await client.get("/d", headers={"if-none-match": hit.headers["etag"]})

    assert again.status_code == 304


async def test_model_hit_matches_miss_exclude_none_alias(client: AsyncClient) -> None:
    miss = await client.get("/m")
    hit = await client.get("/m")

    assert hit.headers["x-fastapi-cache"] == "HIT"
    assert hit.content == miss.content
    body = hit.json()
    assert "opt" not in body
    assert body["Renamed"] == 7
