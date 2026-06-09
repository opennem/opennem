"""Regression tests for optional-auth on the data/market endpoints.

Bug (#555): declaring an endpoint param as ``user: authenticated_user | None = None``
makes FastAPI silently drop the nested ``Depends(get_current_user)`` — the bearer
token is never read, so every request (even with a valid internal/enterprise key)
resolves to ``None`` and is served at anonymous COMMUNITY limits. The fix is the
dedicated ``optional_user`` dependency (``HTTPBearer(auto_error=False)``).

These tests pin the four auth outcomes so the broken pattern can't sneak back.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opennem.api import security
from opennem.api.security import optional_user
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

_INTERNAL_KEY = "oe_internal_TESTKEY_1234567890"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # api_dev_key is a *different* per-env key; the internal key is recognised via
    # api_internal_key — mirroring dev, where api_dev_key != the internal key.
    monkeypatch.setattr(security.settings, "api_dev_key", "on_dev_some_other_key_123")
    monkeypatch.setattr(security.settings, "api_internal_key", _INTERNAL_KEY)

    app = FastAPI()

    @app.get("/probe")
    async def probe(user: optional_user = None) -> dict:
        if user is None:
            return {"auth": "anon", "plan": None, "admin": None}
        return {"auth": "user", "plan": str(user.plan), "admin": bool(user.is_admin)}

    return TestClient(app, raise_server_exceptions=False)


def test_anonymous_request_resolves_to_none(client: TestClient) -> None:
    """No credential → served as anonymous (COMMUNITY limits), not rejected."""
    r = client.get("/probe")
    assert r.status_code == 200
    assert r.json() == {"auth": "anon", "plan": None, "admin": None}


def test_internal_key_resolves_enterprise_admin(client: TestClient) -> None:
    """The internal key (via api_internal_key) grants ENTERPRISE + admin in any env."""
    r = client.get("/probe", headers={"Authorization": f"Bearer {_INTERNAL_KEY}"})
    assert r.status_code == 200
    body = r.json()
    assert body["auth"] == "user"
    assert body["plan"] == str(OpenNEMPlan.ENTERPRISE)
    assert body["admin"] is True


def test_per_env_dev_key_also_resolves_enterprise_admin(client: TestClient) -> None:
    """The per-environment api_dev_key still works as an enterprise+admin bypass."""
    r = client.get("/probe", headers={"Authorization": "Bearer on_dev_some_other_key_123"})
    assert r.status_code == 200
    body = r.json()
    assert body["plan"] == str(OpenNEMPlan.ENTERPRISE)
    assert body["admin"] is True


def test_invalid_key_is_rejected(client: TestClient) -> None:
    """A presented-but-invalid key must 401 (not silently fall back to anon)."""
    with patch.object(security, "unkey_validate", AsyncMock(return_value=None)):
        r = client.get("/probe", headers={"Authorization": "Bearer bogus_key_abcdef"})
    assert r.status_code == 401


def test_valid_unkey_key_resolves_plan(client: TestClient) -> None:
    """A valid Unkey key resolves its plan (here PRO via unkey meta)."""
    fake = OpenNEMUser(
        id="u1",
        owner_id=None,
        plan=OpenNEMPlan.COMMUNITY,
        roles=[OpenNEMRoles.anonymous],
        unkey_meta={"plan": "PRO"},
    )
    with patch.object(security, "unkey_validate", AsyncMock(return_value=fake)):
        r = client.get("/probe", headers={"Authorization": "Bearer valid_unkey_key_123456"})
    assert r.status_code == 200
    body = r.json()
    assert body["auth"] == "user"
    assert body["plan"] == str(OpenNEMPlan.PRO)
    assert body["admin"] is False
