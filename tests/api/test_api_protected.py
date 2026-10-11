"""Legacy api_protected decorator: shared resolver reuse, 403 mapping, no raw key in logs."""

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from opennem.api import keys, security
from opennem.api.keys import api_protected
from opennem.clients.unkey import UnkeyInvalidUserException, UnkeyUnavailableException
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

pytestmark = pytest.mark.asyncio

KEY = "unkey_SECRETKEYVALUE_1234567890"
DEV_KEY = "on_dev_hardcoded_key_1234567"


def _creds(key: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=key)


def _clerk_user(meta: dict[str, str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        first_name="A",
        last_name="B",
        email_addresses=[SimpleNamespace(email_address="a@b.com")],
        private_metadata=meta if meta is not None else {"plan": "BASIC", "role": "admin"},
    )


@pytest.fixture(autouse=True)
def upstream(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    security._user_cache.clear()
    security._invalid_key_cache.clear()
    security._inflight.clear()
    monkeypatch.setattr(security.settings, "api_dev_key", DEV_KEY)
    monkeypatch.setattr(security.settings, "api_internal_key", "oe_internal_x_1234567890")

    unkey = AsyncMock(return_value=OpenNEMUser(id="key_1", owner_id="user_1"))
    clerk_get = AsyncMock(return_value=_clerk_user())
    monkeypatch.setattr(security, "unkey_validate", unkey)
    monkeypatch.setattr(security.clerk_client.users, "get_async", clerk_get, raising=False)
    return SimpleNamespace(unkey=unkey, clerk=clerk_get)


def _endpoint(roles: list[OpenNEMRoles] | None = None):
    @api_protected(roles=roles)
    async def endpoint(authorization: HTTPAuthorizationCredentials | None = None, user: OpenNEMUser | None = None):
        return user

    return endpoint


async def test_valid_key_roles_ok_and_user_injected(upstream: SimpleNamespace) -> None:
    user = await _endpoint([OpenNEMRoles.admin])(authorization=_creds(KEY))
    assert user is not None
    assert user.id == "key_1"
    assert user.plan == OpenNEMPlan.COMMUNITY  # legacy BASIC -> COMMUNITY via shared _resolve_plan
    assert OpenNEMRoles.admin in user.roles
    assert user.email == "a@b.com"


async def test_sync_function_and_no_user_param(upstream: SimpleNamespace) -> None:
    @api_protected()
    def endpoint(authorization: HTTPAuthorizationCredentials | None = None) -> str:
        return "ok"

    assert await endpoint(authorization=_creds(KEY)) == "ok"


async def test_role_mismatch_403(upstream: SimpleNamespace) -> None:
    upstream.clerk.return_value = _clerk_user({"plan": "PRO"})
    with pytest.raises(HTTPException) as exc:
        await _endpoint([OpenNEMRoles.admin])(authorization=_creds(KEY))
    assert exc.value.status_code == 403
    assert exc.value.detail == "Permission denied"


async def test_invalid_key_403_not_401(upstream: SimpleNamespace) -> None:
    upstream.unkey.side_effect = UnkeyInvalidUserException("nope")
    with pytest.raises(HTTPException) as exc:
        await _endpoint()(authorization=_creds(KEY))
    assert exc.value.status_code == 403


async def test_missing_and_short_key_403(upstream: SimpleNamespace) -> None:
    for kwargs in ({}, {"authorization": _creds("short")}):
        with pytest.raises(HTTPException) as exc:
            await _endpoint()(**kwargs)
        assert exc.value.status_code == 403
    upstream.unkey.assert_not_called()


async def test_unkey_timeout_serves_stale(upstream: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> None:
    now = [1000.0]
    monkeypatch.setattr(security, "_now", lambda: now[0])
    first = await _endpoint()(authorization=_creds(KEY))
    now[0] += security.USER_CACHE_TTL_S + 60
    upstream.unkey.side_effect = UnkeyUnavailableException("timeout")
    stale = await _endpoint()(authorization=_creds(KEY))
    assert stale is not None and first is not None
    assert stale.id == first.id


async def test_dev_key_bypass_unchanged(upstream: SimpleNamespace) -> None:
    user = await _endpoint([OpenNEMRoles.admin])(authorization=_creds(DEV_KEY))
    assert user is not None
    assert user.id == "dev"
    assert user.plan == OpenNEMPlan.ENTERPRISE
    upstream.unkey.assert_not_called()
    upstream.clerk.assert_not_called()


async def test_on_exc_handler_receives_exception(upstream: SimpleNamespace) -> None:
    @api_protected(on_exc=lambda exc: getattr(exc, "status_code", None))
    async def endpoint(authorization: HTTPAuthorizationCredentials | None = None) -> str:
        return "ok"

    assert await endpoint(authorization=_creds("short")) == 403


@pytest.fixture
def captured(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> pytest.LogCaptureFixture:
    """opennem loggers may not propagate to root: attach the capture handler to each directly."""
    caplog.set_level(logging.DEBUG)
    for name in ("opennem", "opennem.api.keys", "opennem.api.security", "opennem.clients.unkey"):
        lg = logging.getLogger(name)
        monkeypatch.setattr(lg, "handlers", [*lg.handlers, caplog.handler])
        monkeypatch.setattr(lg, "level", logging.DEBUG)
    return caplog


def _no_key_in(caplog: pytest.LogCaptureFixture, key: str) -> None:
    fragments = {key, *(key[i : i + 12] for i in range(len(key) - 11))}
    for record in caplog.records:
        text = record.getMessage() + " " + str(record.__dict__.get("exc_text") or "")
        assert not any(f in text for f in fragments), f"key leaked in log: {record.name} {record.levelname}"


async def test_failed_auth_never_logs_key(upstream: SimpleNamespace, captured: pytest.LogCaptureFixture) -> None:
    caplog = captured
    upstream.unkey.side_effect = UnkeyInvalidUserException("Verification failed: not valid")
    short_key = "shortkey_1"  # len == 10: rejected as too short by legacy check

    for key in (KEY, short_key):
        with pytest.raises(HTTPException):
            await _endpoint()(authorization=_creds(key))
    with pytest.raises(HTTPException):
        await _endpoint()()  # missing key

    assert caplog.records
    _no_key_in(caplog, KEY)
    _no_key_in(caplog, short_key)


async def test_unavailable_auth_never_logs_key(upstream: SimpleNamespace, captured: pytest.LogCaptureFixture) -> None:
    caplog = captured
    upstream.unkey.side_effect = UnkeyUnavailableException("Unkey unreachable: TimeoutError")
    with pytest.raises(HTTPException):
        await _endpoint()(authorization=_creds(KEY))
    _no_key_in(caplog, KEY)


def test_key_fingerprint_short_and_not_a_prefix() -> None:
    fp = security.key_fingerprint(KEY)
    assert len(fp) == 8
    assert fp not in KEY
    assert keys.api_protected is api_protected
