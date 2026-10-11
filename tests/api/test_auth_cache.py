"""Auth cache: enriched-user cache, single-flight, stale-if-error, negative cache (mocked Unkey + Clerk)."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from opennem.api import security
from opennem.clients.unkey import UnkeyInvalidUserException, UnkeyUnavailableException
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

pytestmark = pytest.mark.asyncio

KEY = "unkey_test_key_1234567890"


def _unkey_user() -> OpenNEMUser:
    return OpenNEMUser(id="key_1", owner_id="user_1", unkey_meta={"plan": "PRO"})


def _clerk_user() -> SimpleNamespace:
    return SimpleNamespace(
        first_name="A",
        last_name="B",
        email_addresses=[SimpleNamespace(email_address="a@b.com")],
        private_metadata={"plan": "PRO"},
    )


@pytest.fixture(autouse=True)
def upstream(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    security._user_cache.clear()
    security._invalid_key_cache.clear()
    security._inflight.clear()
    monkeypatch.setattr(security.settings, "api_dev_key", "on_dev_some_other_key_123")
    monkeypatch.setattr(security.settings, "api_internal_key", "oe_internal_x_1234567890")

    async def unkey_side_effect(api_key: str) -> OpenNEMUser:
        await asyncio.sleep(0.01)  # let concurrent callers pile up
        return _unkey_user()

    unkey = AsyncMock(side_effect=unkey_side_effect)
    clerk_get = AsyncMock(return_value=_clerk_user())
    monkeypatch.setattr(security, "unkey_validate", unkey)
    monkeypatch.setattr(security.clerk_client.users, "get_async", clerk_get, raising=False)
    return SimpleNamespace(unkey=unkey, clerk=clerk_get)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    now = [1000.0]
    monkeypatch.setattr(security, "_now", lambda: now[0])
    return now


async def test_cache_hit_zero_upstream_calls(upstream: SimpleNamespace) -> None:
    first = await security._resolve_user_from_key(KEY)
    second = await security._resolve_user_from_key(KEY)

    assert first.plan == OpenNEMPlan.PRO and second.email == "a@b.com"
    assert upstream.unkey.await_count == 1
    assert upstream.clerk.await_count == 1


async def test_concurrent_misses_single_flight(upstream: SimpleNamespace) -> None:
    users = await asyncio.gather(*[security._resolve_user_from_key(KEY) for _ in range(20)])

    assert upstream.unkey.await_count == 1
    assert upstream.clerk.await_count == 1
    assert len({id(u) for u in users}) == 20  # each caller gets its own copy


async def test_timeout_serves_stale(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += security.USER_CACHE_TTL_S + 60  # expired, within stale window
    upstream.unkey.side_effect = UnkeyUnavailableException("timeout")

    user = await security._resolve_user_from_key(KEY)

    assert user.id == "key_1" and user.plan == OpenNEMPlan.PRO
    assert upstream.unkey.await_count == 2


async def test_clerk_error_serves_stale(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += security.USER_CACHE_TTL_S + 1
    upstream.clerk.side_effect = TimeoutError()

    assert (await security._resolve_user_from_key(KEY)).email == "a@b.com"


async def test_stale_beyond_cap_fails(upstream: SimpleNamespace, clock: list[float]) -> None:
    await security._resolve_user_from_key(KEY)
    clock[0] += security.USER_CACHE_TTL_S + security.USER_CACHE_MAX_STALE_S + 1
    upstream.unkey.side_effect = UnkeyUnavailableException("timeout")

    with pytest.raises(HTTPException) as exc:
        await security._resolve_user_from_key(KEY)

    assert exc.value.status_code == 401


async def test_timeout_without_cache_fails_and_is_not_negative_cached(upstream: SimpleNamespace) -> None:
    upstream.unkey.side_effect = UnkeyUnavailableException("timeout")
    with pytest.raises(HTTPException) as exc:
        await security._resolve_user_from_key(KEY)
    assert exc.value.status_code == 401

    # upstream recovers: next request must go upstream again and succeed
    upstream.unkey.side_effect = None
    upstream.unkey.return_value = _unkey_user()
    assert (await security._resolve_user_from_key(KEY)).id == "key_1"
    assert upstream.unkey.await_count == 2


async def test_invalid_key_negative_cached(upstream: SimpleNamespace, clock: list[float]) -> None:
    upstream.unkey.side_effect = UnkeyInvalidUserException("not valid")

    for _ in range(3):
        with pytest.raises(HTTPException) as exc:
            await security._resolve_user_from_key(KEY)
        assert exc.value.status_code == 401 and exc.value.detail == "Invalid API key"

    assert upstream.unkey.await_count == 1

    clock[0] += security.NEGATIVE_CACHE_TTL_S + 1
    with pytest.raises(HTTPException):
        await security._resolve_user_from_key(KEY)
    assert upstream.unkey.await_count == 2


async def test_returned_user_mutation_does_not_poison_cache(upstream: SimpleNamespace) -> None:
    first = await security._resolve_user_from_key(KEY)
    first.roles.append(OpenNEMRoles.admin)
    first.plan = OpenNEMPlan.ENTERPRISE
    first.email = "evil@x.com"

    second = await security._resolve_user_from_key(KEY)
    assert OpenNEMRoles.admin not in second.roles
    assert second.plan == OpenNEMPlan.PRO and second.email == "a@b.com"

    second.roles.append(OpenNEMRoles.admin)
    assert OpenNEMRoles.admin not in (await security._resolve_user_from_key(KEY)).roles


async def test_dev_key_bypass_unchanged(upstream: SimpleNamespace) -> None:
    user = await security._resolve_user_from_key("on_dev_some_other_key_123")

    assert user.id == "dev" and OpenNEMRoles.admin in user.roles
    assert upstream.unkey.await_count == 0


def _verify_response(valid: bool) -> SimpleNamespace:
    data = SimpleNamespace(
        valid=valid,
        key_id="key_1",
        identity=SimpleNamespace(external_id="user_1"),
        meta=None,
        credits=None,
        expires=None,
        ratelimits=None,
    )
    return SimpleNamespace(data=data)


def _fake_unkey(monkeypatch: pytest.MonkeyPatch, verify: AsyncMock) -> None:
    from opennem.clients import unkey as unkey_mod

    monkeypatch.setattr(unkey_mod.settings, "unkey_root_key", "root")
    monkeypatch.setattr(unkey_mod, "_get_unkey_client", lambda: SimpleNamespace(keys=SimpleNamespace(verify_key_async=verify)))


async def test_unkey_validate_retries_once_then_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.clients import unkey as unkey_mod

    verify = AsyncMock(side_effect=[TimeoutError(), _verify_response(True)])
    _fake_unkey(monkeypatch, verify)

    user = await unkey_mod.unkey_validate(api_key=KEY)

    assert user and user.id == "key_1" and verify.await_count == 2


async def test_unkey_validate_timeout_is_unavailable_not_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.clients import unkey as unkey_mod

    verify = AsyncMock(side_effect=TimeoutError())
    _fake_unkey(monkeypatch, verify)

    with pytest.raises(UnkeyUnavailableException):
        await unkey_mod.unkey_validate(api_key=KEY)
    assert verify.await_count == 2


async def test_unkey_validate_invalid_key_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.clients import unkey as unkey_mod

    verify = AsyncMock(return_value=_verify_response(False))
    _fake_unkey(monkeypatch, verify)

    with pytest.raises(UnkeyInvalidUserException) as exc:
        await unkey_mod.unkey_validate(api_key=KEY)
    assert not isinstance(exc.value, UnkeyUnavailableException) and verify.await_count == 1


async def test_fresh_bypasses_cache_but_other_calls_use_it(upstream: SimpleNamespace) -> None:
    await security._resolve_user_from_key(KEY)
    assert upstream.unkey.await_count == 1

    await security._resolve_user_from_key(KEY)  # normal endpoint: cache hit
    assert upstream.unkey.await_count == 1

    await security._resolve_user_from_key(KEY, fresh=True)  # /me: upstream despite fresh entry
    assert upstream.unkey.await_count == 2
    assert upstream.clerk.await_count == 2


async def test_fresh_refreshes_cache_entry(upstream: SimpleNamespace) -> None:
    await security._resolve_user_from_key(KEY)
    upstream.clerk.return_value = SimpleNamespace(
        first_name="New",
        last_name="Name",
        email_addresses=[SimpleNamespace(email_address="n@b.com")],
        private_metadata={"plan": "PRO"},
    )

    assert (await security._resolve_user_from_key(KEY, fresh=True)).email == "n@b.com"
    assert (await security._resolve_user_from_key(KEY)).email == "n@b.com"
    assert upstream.unkey.await_count == 2


async def test_fresh_falls_back_to_stale_on_timeout(upstream: SimpleNamespace) -> None:
    await security._resolve_user_from_key(KEY)  # entry is fresh, not expired
    upstream.unkey.side_effect = UnkeyUnavailableException("timeout")

    user = await security._resolve_user_from_key(KEY, fresh=True)

    assert user.id == "key_1" and user.email == "a@b.com"


async def test_fresh_concurrent_single_flight(upstream: SimpleNamespace) -> None:
    await asyncio.gather(*[security._resolve_user_from_key(KEY, fresh=True) for _ in range(10)])

    assert upstream.unkey.await_count == 1
