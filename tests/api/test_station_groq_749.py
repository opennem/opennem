"""Regression tests for #749: caller input must never be interpolated into GROQ."""

from collections.abc import AsyncIterator, Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import quote

import pytest
import pytest_asyncio
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import ASGITransport, AsyncClient

from opennem.api.app import app
from opennem.api.security import get_current_user
from opennem.api.station import router as station
from opennem.cms import queries
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit

pytestmark = pytest.mark.asyncio

EVIL = "BAYSW' || true || code == '"


def _user() -> OpenNEMUser:
    return OpenNEMUser(
        id="u",
        plan=OpenNEMPlan.COMMUNITY,
        roles=[OpenNEMRoles.anonymous],
        rate_limit=OpenNEMUserRateLimit(limit=60, remaining=5, reset=1_700_000_000_000),
    )


@pytest_asyncio.fixture(autouse=True)
async def _cache() -> AsyncIterator[None]:
    InMemoryBackend._store.clear()
    FastAPICache.init(InMemoryBackend(), prefix="test")
    station._inflight.clear()
    yield
    FastAPICache.reset()
    app.dependency_overrides.clear()


@pytest.fixture
def authed() -> Iterator[None]:
    app.dependency_overrides[get_current_user] = lambda: _user()
    yield
    app.dependency_overrides.pop(get_current_user, None)


class _FakeSanity:
    """Stands in for SanityAsyncClient as an async context manager."""

    def __init__(self, response: Any = None) -> None:
        self.query = AsyncMock(return_value=response if response is not None else {"result": []})

    def __call__(self, *a: Any, **kw: Any) -> "_FakeSanity":
        return self

    async def __aenter__(self) -> "_FakeSanity":
        return self

    async def __aexit__(self, *a: Any) -> None:
        return None


@pytest.mark.parametrize(
    "code",
    [
        "BAY'SW",
        'BAY"SW',
        "BAY[0]",
        "A||B",
        "BAY]",
        "BAY%0ASW",
        "BAY SW",
        "BAYSWé",
        "中文",
        "BAYSW/extra",
        "a" * 65,
        "BAY%27%20%7C%7C%20true",
    ],
)
async def test_bad_codes_404_without_cms(monkeypatch: pytest.MonkeyPatch, authed: None, code: str) -> None:
    cms = AsyncMock(return_value=[])
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    fake = _FakeSanity()
    monkeypatch.setattr(queries, "SanityAsyncClient", fake)
    path = code if "%" in code else quote(code, safe="/")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get(f"/v4/facility/au/NEM/{path}")
    assert r.status_code == 404
    assert cms.await_count == 0
    assert fake.query.await_count == 0


@pytest.mark.parametrize("code", ["BAYSW", "0BSSF", "COLLIE_G1", "AB-1", "AU.X1"])
async def test_valid_codes_reach_cms(monkeypatch: pytest.MonkeyPatch, authed: None, code: str) -> None:
    cms = AsyncMock(return_value=[])
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get(f"/v4/facility/au/NEM/{code}")
    assert r.status_code == 404  # empty CMS result: same body as before
    assert r.json()["error"] == "Station not found"  # same body as an unknown code
    cms.assert_awaited_once_with(facility_code=code)


async def test_facilities_query_uses_params(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSanity()
    monkeypatch.setattr(queries, "SanityAsyncClient", fake)
    await queries.get_cms_facilities.__wrapped__(facility_code=EVIL, cms_id="id' || true")  # pyright: ignore[reportFunctionMemberAccess]
    assert fake.query.await_args is not None
    args, kwargs = fake.query.await_args
    assert "BAYSW" not in args[0] and "true" not in args[0] and "||" not in args[0]
    assert "code == $code" in args[0]
    assert "_id == $cms_id" in args[0]
    assert kwargs["variables"] == {"code": EVIL, "cms_id": "id' || true"}
    assert kwargs["method"] == "POST"


async def test_facilities_query_no_filter_no_params(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSanity()
    monkeypatch.setattr(queries, "SanityAsyncClient", fake)
    await queries.get_cms_facilities.__wrapped__()  # pyright: ignore[reportFunctionMemberAccess]
    assert fake.query.await_args is not None
    args, kwargs = fake.query.await_args
    assert "$" not in args[0]
    assert kwargs["variables"] is None


async def test_unit_query_uses_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.query.return_value = {"result": []}
    monkeypatch.setattr(queries, "sanity_client", client)
    with pytest.raises(queries.CMSQueryError):
        queries.get_cms_unit(EVIL)
    args, kwargs = client.query.call_args
    assert "BAYSW" not in args[0] and "||" not in args[0]
    assert "code == $code" in args[0]
    assert kwargs["variables"] == {"code": EVIL}
    assert kwargs["method"] == "POST"
