"""admin_user dependency on the real app: Clerk admin only, bypass keys rejected (mocked Unkey + Clerk)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from opennem.api import security
from opennem.api.app import app
from opennem.clients.unkey import UnkeyInvalidUserException
from opennem.users.schema import OpenNEMUser

DEV_KEY = "on_dev_bypass_key_1234567890"
INTERNAL_KEY = "oe_internal_x_1234567890"
REAL_KEY = "unkey_real_admin_1234567890"
PATH = f"/v4/admin/social/{uuid4()}"


def _clerk(private_metadata: dict | None) -> SimpleNamespace:
    return SimpleNamespace(
        first_name="A",
        last_name="B",
        email_addresses=[SimpleNamespace(email_address="a@b.com")],
        private_metadata=private_metadata,
    )


@pytest.fixture
def upstream(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    security._user_cache.clear()
    security._invalid_key_cache.clear()
    monkeypatch.setattr(security.settings, "api_dev_key", DEV_KEY)
    monkeypatch.setattr(security.settings, "api_internal_key", INTERNAL_KEY)
    unkey = AsyncMock(
        side_effect=lambda api_key: OpenNEMUser(id="key_1", owner_id="user_1")
    )  # new user per call: resolver mutates roles
    clerk = AsyncMock(return_value=_clerk({"role": "admin"}))
    monkeypatch.setattr(security, "unkey_validate", unkey)
    monkeypatch.setattr(security.clerk_client.users, "get_async", clerk, raising=False)
    return SimpleNamespace(unkey=unkey, clerk=clerk)


def _get(key: str | None) -> int:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    with patch("opennem.api.admin.social.get_social_post", AsyncMock(return_value={"id": "x"})):
        return TestClient(app).get(PATH, headers=headers).status_code


def test_clerk_admin_allowed(upstream: SimpleNamespace) -> None:
    assert _get(REAL_KEY) == 200


def test_clerk_non_admin_forbidden(upstream: SimpleNamespace) -> None:
    upstream.clerk.return_value = _clerk({"plan": "PRO"})
    assert _get(REAL_KEY) == 403


def test_unkey_admin_role_without_clerk_owner_forbidden(upstream: SimpleNamespace) -> None:
    upstream.unkey.side_effect = lambda api_key: OpenNEMUser(id="key_1", owner_id=None, roles=[security.OpenNEMRoles.admin])
    assert _get(REAL_KEY) == 403


@pytest.mark.parametrize("key", [DEV_KEY, INTERNAL_KEY])
def test_bypass_keys_forbidden_without_upstream_calls(upstream: SimpleNamespace, key: str) -> None:
    assert _get(key) == 403
    upstream.unkey.assert_not_awaited()
    upstream.clerk.assert_not_awaited()


def test_bypass_user_from_resolver_forbidden(upstream: SimpleNamespace) -> None:
    """defence in depth: even if the resolver hands back the bypass user for another key"""
    with patch.object(security, "_resolve_user_from_key", AsyncMock(return_value=security._OPENNEM_INTERNAL_USER.model_copy())):
        assert _get(REAL_KEY) == 403


def test_invalid_key_unauthorized(upstream: SimpleNamespace) -> None:
    upstream.unkey.side_effect = UnkeyInvalidUserException("bad")
    assert _get("not_a_real_key_1234567890") == 401


def test_no_key_unauthorized(upstream: SimpleNamespace) -> None:
    assert _get(None) == 401


def test_admin_role_is_read_fresh(upstream: SimpleNamespace) -> None:
    assert _get(REAL_KEY) == 200
    upstream.clerk.return_value = _clerk({})  # admin revoked
    assert _get(REAL_KEY) == 403
