"""Cache-hit tests: repeat calls from different users/clients on one tier hit; other tiers miss."""

from collections.abc import AsyncIterator
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from opennem.api.data import router as data_router
from opennem.api.facilities import router as facilities_router
from opennem.api.market import router as market_router
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit

pytestmark = pytest.mark.asyncio

_START = datetime(2026, 1, 1)
_END = datetime(2026, 1, 2)


@pytest_asyncio.fixture(autouse=True)
async def _cache() -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend(), prefix="test")
    yield
    FastAPICache.reset()


def _user(uid: str, plan: OpenNEMPlan = OpenNEMPlan.COMMUNITY, remaining: int = 5) -> OpenNEMUser:
    return OpenNEMUser(
        id=uid,
        plan=plan,
        roles=[OpenNEMRoles.anonymous],
        rate_limit=OpenNEMUserRateLimit(limit=60, remaining=remaining, reset=1_700_000_000_000),
    )


def _patch_ts(monkeypatch: pytest.MonkeyPatch, mod: Any) -> MagicMock:
    """Stub the query/format pipeline; the returned mock counts executed queries."""
    execute = AsyncMock(return_value=[("x",)])
    monkeypatch.setattr(mod, "validate_date_range", lambda **kw: (_START, _END))
    monkeypatch.setattr(mod, "get_timeseries_query", lambda **kw: ("q", {}, ["c"]))
    monkeypatch.setattr(mod, "execute_async", execute)
    monkeypatch.setattr(mod, "format_timeseries_response", lambda **kw: [])
    monkeypatch.setattr(mod, "build_timeseries_response", lambda ts: {"data": []})
    return execute


async def _assert_hits(call: Any, counter: MagicMock) -> None:
    await call(user=_user("a", remaining=1), client=object())
    await call(user=_user("b", remaining=50), client=object())
    assert counter.call_count == 1, "second user on same tier must hit cache"
    await call(user=_user("c", plan=OpenNEMPlan.PRO), client=object())
    assert counter.call_count == 2, "different tier must miss cache"


async def test_data_network_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    execute = _patch_ts(monkeypatch, data_router)

    async def call(**kw: Any) -> Any:
        return await data_router.get_network_data(
            network_code="NEM", metrics=[Metric.ENERGY], interval=Interval.INTERVAL, date_start=_START, date_end=_END,
            network_region=None, fueltech=None, fueltech_group=None, **kw,
        )  # fmt: skip

    await _assert_hits(call, execute)


async def test_data_facilities_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    execute = _patch_ts(monkeypatch, data_router)

    async def call(**kw: Any) -> Any:
        return await data_router.get_facility_data(
            network_code="NEM", metrics=[Metric.ENERGY], interval=Interval.INTERVAL, facility_code=["BAYSW"],
            unit_code=None, date_start=_START, date_end=_END, **kw,
        )  # fmt: skip

    await _assert_hits(call, execute)


async def test_market_network_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    actual = AsyncMock(return_value=([{"metric": "price"}], True))
    monkeypatch.setattr(market_router, "_actual_timeseries", actual)
    monkeypatch.setattr(market_router, "build_timeseries_response", lambda ts: {"data": ts})

    async def call(**kw: Any) -> Any:
        return await market_router.get_network_data(
            network_code="NEM", metrics=[Metric.PRICE], interval=Interval.INTERVAL, date_start=_START, date_end=_END,
            network_region=None, **kw,
        )  # fmt: skip

    await _assert_hits(call, actual)


async def test_get_facilities_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    unit = SimpleNamespace(
        code="U1", code_display="U1", fueltech_id="wind", status_id="retired", approved=True, interconnector=False,
        capacity_registered=None, capacity_maximum=None, capacity_storage=None, emissions_factor_co2=None,
        data_first_seen=None, data_last_seen=None, dispatch_type=None, commencement_date=None, closure_date=None,
        expected_operation_date=None, expected_closure_date=None, construction_start_date=None,
        project_approval_date=None, project_approval_lodgement_date=None, commencement_date_specificity=None,
        closure_date_specificity=None, expected_operation_date_specificity=None, expected_closure_date_specificity=None,
        construction_start_date_specificity=None, project_approval_date_specificity=None, cms_created_at=None,
        cms_updated_at=None, max_generation=None, max_generation_interval=None,
    )  # fmt: skip
    facility = SimpleNamespace(
        code="F1", code_display="F1", name="F", network_id="NEM", network_region="NSW1", description=None, npi_id=None,
        osm_way_id=None, location=None, boundary=None, units=[unit], cms_created_at=None, cms_updated_at=None,
    )  # fmt: skip
    opened = MagicMock()

    class _Session:
        async def __aenter__(self) -> "_Session":
            opened()
            return self

        async def __aexit__(self, *a: Any) -> None:
            return None

        async def execute(self, stmt: Any) -> Any:
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [facility]))

    monkeypatch.setattr(facilities_router, "get_read_session", lambda: _Session())

    async def call(**kw: Any) -> Any:
        kw.pop("client")
        return await facilities_router.get_facilities(
            facility_code=None, status_id=None, fueltech_id=None, fueltech_group_id=None, network_id=None,
            network_region=None, **kw,
        )  # fmt: skip

    await _assert_hits(call, opened)
