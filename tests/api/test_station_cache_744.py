"""Station routes cache (#744): cache below @router.get, auth still enforced on hits, errors never cached."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import ASGITransport, AsyncClient

from opennem.api.app import app
from opennem.api.security import get_current_user
from opennem.api.station import router as station
from opennem.schema.facility import FacilitySchema
from opennem.schema.unit import UnitFueltechType
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit

pytestmark = pytest.mark.asyncio

ONE = "/v4/facility/au/NEM/BAYSW"


def _user(plan: OpenNEMPlan = OpenNEMPlan.COMMUNITY) -> OpenNEMUser:
    return OpenNEMUser(
        id="u",
        plan=plan,
        roles=[OpenNEMRoles.anonymous],
        rate_limit=OpenNEMUserRateLimit(limit=60, remaining=5, reset=1_700_000_000_000),
    )


def _facility(code: str = "BAYSW", fueltechs: tuple[str, ...] = ("coal_black",)) -> Any:
    units = [
        {"code": f"{code}{i}", "fueltech_id": ft, "status_id": "operating", "dispatch_type": "GENERATOR"}
        for i, ft in enumerate(fueltechs)
    ]
    return FacilitySchema.model_validate(
        {"code": code, "name": code, "network_id": "NEM", "network_region": "NSW1", "units": units}
    )


@pytest_asyncio.fixture(autouse=True)
async def _cache() -> AsyncIterator[None]:
    InMemoryBackend._store.clear()  # class-level store shared across instances
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


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_single_facility_second_call_hits(monkeypatch: pytest.MonkeyPatch, authed: None) -> None:
    cms = AsyncMock(return_value=[_facility()])
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with _client() as c:
        miss = await c.get(ONE)
        hit = await c.get(ONE)
    assert miss.status_code == hit.status_code == 200
    assert cms.await_count == 1
    assert hit.content == miss.content


async def test_list_second_call_hits(monkeypatch: pytest.MonkeyPatch, authed: None) -> None:
    cms = AsyncMock(return_value=[_facility()])
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with _client() as c:
        miss = await c.get("/v4/facility/")
        hit = await c.get("/v4/facility/")
    assert cms.await_count == 1
    assert hit.content == miss.content
    assert miss.json()["total_records"] == 1


async def test_body_matches_uncached_schema(monkeypatch: pytest.MonkeyPatch, authed: None) -> None:
    """Miss bytes honour exclude_none like FastAPI's own serialisation."""
    monkeypatch.setattr(station, "get_cms_facilities", AsyncMock(return_value=[_facility()]))
    async with _client() as c:
        body = (await c.get(ONE)).json()
    assert "error" not in body  # None field excluded
    assert body["data"][0]["code"] == "BAYSW"


async def test_different_codes_different_keys(monkeypatch: pytest.MonkeyPatch, authed: None) -> None:
    async def fake(facility_code: str | None = None, cms_id: str | None = None) -> list[Any]:
        return [_facility(facility_code or "X")]

    cms = AsyncMock(side_effect=fake)
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with _client() as c:
        a = await c.get("/v4/facility/au/NEM/AAA")
        b = await c.get("/v4/facility/au/NEM/BBB")
        await c.get("/v4/facility/au/NEM/AAA")
    assert cms.await_count == 2
    assert a.json()["data"][0]["code"] == "AAA"
    assert b.json()["data"][0]["code"] == "BBB"


async def test_errors_not_cached(monkeypatch: pytest.MonkeyPatch, authed: None) -> None:
    cms = AsyncMock(return_value=[])
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with _client() as c:
        assert (await c.get(ONE)).status_code == 404
        assert (await c.get(ONE)).status_code == 404
        assert cms.await_count == 2  # not-found refetched
        assert (await c.get("/v4/facility/au/XXX/BAYSW")).status_code == 404
        assert cms.await_count == 2  # bad network rejected before cms
        # station exists later: not stuck behind a cached 404
        cms.return_value = [_facility()]
        assert (await c.get(ONE)).status_code == 200


async def test_battery_only_station_404_not_cached(monkeypatch: pytest.MonkeyPatch, authed: None) -> None:
    cms = AsyncMock(return_value=[_facility(fueltechs=(UnitFueltechType.battery.value,))])
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with _client() as c:
        assert (await c.get(ONE)).status_code == 404
        assert (await c.get(ONE)).status_code == 404
    assert cms.await_count == 2


async def test_auth_enforced_on_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    cms = AsyncMock(return_value=[_facility()])
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with _client() as c:
        app.dependency_overrides[get_current_user] = lambda: _user()
        assert (await c.get(ONE)).status_code == 200
        assert (await c.get(ONE)).status_code == 200
        assert cms.await_count == 1

        def deny() -> None:
            raise HTTPException(status_code=401, detail="unauthorised")

        app.dependency_overrides[get_current_user] = deny
        assert (await c.get(ONE)).status_code == 401
        assert (await c.get("/v4/facility/")).status_code == 401
    assert cms.await_count == 1


async def test_concurrent_misses_coalesce(monkeypatch: pytest.MonkeyPatch, authed: None) -> None:
    gate = asyncio.Event()

    async def slow(facility_code: str | None = None, cms_id: str | None = None) -> list[Any]:
        await gate.wait()
        return [_facility()]

    cms = AsyncMock(side_effect=slow)
    monkeypatch.setattr(station, "get_cms_facilities", cms)
    async with _client() as c:
        tasks = [asyncio.ensure_future(c.get(ONE)) for _ in range(5)]
        await asyncio.sleep(0.2)
        gate.set()
        rs = await asyncio.gather(*tasks)
    assert cms.await_count == 1
    assert {r.content for r in rs} and len({r.content for r in rs}) == 1
    assert station._inflight == {}


async def test_route_versions_unchanged() -> None:
    paths = {getattr(r, "path", "") for r in app.routes}
    for prefix in ("/v1", "/v3", "/v4", ""):
        assert f"{prefix}/facility/au/{{network_id}}/{{station_code:path}}" in paths
        assert f"{prefix}/facility/" in paths
