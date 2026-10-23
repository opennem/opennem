"""Auth cache stale-while-revalidate (#743): serve stale instantly, one background refresh per key."""

import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import HTTPException

from opennem.api import security
from opennem.clients.unkey import UnkeyInvalidUserException, UnkeyUnavailableException
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMUser

pytestmark = pytest.mark.asyncio

KEY = "unkey_test_key_1234567890"
TTL = security.USER_CACHE_TTL_S
STALE = security.USER_CACHE_MAX_STALE_S


def _clerk_user(plan: str) -> SimpleNamespace:
    return SimpleNamespace(
        first_name="A",
        last_name="B",
        email_addresses=[SimpleNamespace(email_address="a@b.com")],
        private_metadata={"plan": plan},
    )


@pytest_asyncio.fixture(autouse=True)
async def upstream(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[SimpleNamespace]:
    security._user_cache.clear()
    security._invalid_key_cache.clear()
    security._inflight.clear()
    security._background_refreshes.clear()
    monkeypatch.setattr(security.settings, "api_dev_key", "on_dev_some_other_key_123")
    monkeypatch.setattr(security.settings, "api_internal_key", "oe_internal_x_1234567890")

    async def unkey_side_effect(api_key: str) -> OpenNEMUser:
        await asyncio.sleep(0.01)
        return OpenNEMUser(id="key_1", owner_id="user_1")

    unkey = AsyncMock(side_effect=unkey_side_effect)
    clerk = AsyncMock(return_value=_clerk_user("PRO"))
    monkeypatch.setattr(security, "unkey_validate", unkey)
    monkeypatch.setattr(security.clerk_client.users, "get_async", clerk, raising=False)
    yield SimpleNamespace(unkey=unkey, clerk=clerk)
    await security.cancel_background_refreshes()


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    now = [1000.0]
    monkeypatch.setattr(security, "_now", lambda: now[0])
    return now


async def _drain() -> None:
    await asyncio.gather(*security._background_refreshes.values(), return_exceptions=True)


async def test_fresh_hit_no_upstream_no_refresh(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL - 1
    await security._resolve_user_from_key(KEY)

    assert not security._background_refreshes
    assert upstream.unkey.await_count == 1


async def test_stale_hit_returns_immediately_one_refresh_for_20_requests(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL + 1

    users = await asyncio.gather(*[security._resolve_user_from_key(KEY) for _ in range(20)])

    assert all(u.plan == OpenNEMPlan.PRO for u in users)
    assert upstream.unkey.await_count == 2  # exactly one refresh started for 20 callers
    assert len(security._background_refreshes) == 1  # still running: callers did not wait
    await _drain()
    assert upstream.unkey.await_count == 2 and upstream.clerk.await_count == 2
    # entry renewed: next request is a plain fresh hit
    await security._resolve_user_from_key(KEY)
    assert upstream.unkey.await_count == 2 and not security._background_refreshes


async def test_foreground_miss_and_background_refresh_share_flight(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL + 1
    await security._resolve_user_from_key(KEY)  # schedules refresh
    await asyncio.sleep(0)  # let the refresh start its fetch
    await security._resolve_user_from_key(KEY, fresh=True)  # joins in-flight fetch
    await _drain()

    assert upstream.unkey.await_count == 2


async def test_refresh_failure_keeps_stale_and_next_request_retries(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL + 1
    upstream.unkey.side_effect = UnkeyUnavailableException("down")

    assert (await security._resolve_user_from_key(KEY)).id == "key_1"
    await _drain()
    assert upstream.unkey.await_count == 2
    assert security._user_cache.get(security._cache_key(KEY)) is not None

    assert (await security._resolve_user_from_key(KEY)).id == "key_1"  # still served
    await _drain()
    assert upstream.unkey.await_count == 3  # retried


async def test_plan_change_visible_after_refresh(upstream: SimpleNamespace, clock: list[float]) -> None:
    assert (await security._resolve_user_from_key(KEY)).plan == OpenNEMPlan.PRO
    clock[0] += TTL + 1
    upstream.clerk.return_value = _clerk_user("COMMUNITY")

    assert (await security._resolve_user_from_key(KEY)).plan == OpenNEMPlan.PRO  # stale served once
    await _drain()
    assert (await security._resolve_user_from_key(KEY)).plan == OpenNEMPlan.COMMUNITY


async def test_beyond_max_stale_blocks_and_refreshes(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL + STALE + 1
    upstream.clerk.return_value = _clerk_user("COMMUNITY")

    user = await security._resolve_user_from_key(KEY)

    assert user.plan == OpenNEMPlan.COMMUNITY  # blocked on upstream, no stale serve
    assert not security._background_refreshes
    assert upstream.unkey.await_count == 2


async def test_invalid_key_from_refresh_evicts_and_negative_caches(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL + 1
    upstream.unkey.side_effect = UnkeyInvalidUserException("revoked")

    await security._resolve_user_from_key(KEY)  # stale served
    await _drain()

    ckey = security._cache_key(KEY)
    assert ckey not in security._user_cache and ckey in security._invalid_key_cache
    with pytest.raises(HTTPException) as exc:
        await security._resolve_user_from_key(KEY)
    assert exc.value.status_code == 401


async def test_fresh_true_blocks_and_refreshes_cache(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL + 1
    upstream.clerk.return_value = _clerk_user("COMMUNITY")

    user = await security._resolve_user_from_key(KEY, fresh=True)

    assert user.plan == OpenNEMPlan.COMMUNITY
    assert not security._background_refreshes
    clock[0] += 1
    assert (await security._resolve_user_from_key(KEY)).plan == OpenNEMPlan.COMMUNITY
    assert upstream.unkey.await_count == 2


async def test_is_key_known_valid_false_for_stale(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    assert security.is_key_known_valid(KEY)
    clock[0] += TTL + 1
    assert not security.is_key_known_valid(KEY)


async def test_cancel_background_refreshes(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += TTL + 1
    await security._resolve_user_from_key(KEY)
    await security.cancel_background_refreshes()

    assert not security._background_refreshes
