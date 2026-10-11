"""/v4/admin/social handlers: right pipeline function, admin identity; old /v4/social is gone."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from opennem.api.app import app
from opennem.api.security import get_admin_user
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

POST_ID = uuid4()
ADMIN = OpenNEMUser(id="user_1", owner_id="user_1", email="admin@example.com", roles=[OpenNEMRoles.admin])
BASE = "/v4/admin/social"
M = "opennem.api.admin.social"


@pytest.fixture
def client() -> Generator[TestClient]:
    app.dependency_overrides[get_admin_user] = lambda: ADMIN
    yield TestClient(app)
    app.dependency_overrides.pop(get_admin_user, None)


def test_get_post(client: TestClient) -> None:
    with patch(f"{M}.get_social_post", AsyncMock(return_value={"id": "p"})) as get:
        r = client.get(f"{BASE}/{POST_ID}")
    assert r.status_code == 200 and r.json()["data"] == {"id": "p"}
    get.assert_awaited_once_with(POST_ID)


def test_get_post_404(client: TestClient) -> None:
    with patch(f"{M}.get_social_post", AsyncMock(return_value=None)):
        assert client.get(f"{BASE}/{POST_ID}").status_code == 404


def test_list_posts(client: TestClient) -> None:
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    with patch(f"{M}.get_read_session", return_value=ctx):
        r = client.get(BASE, params={"status": "draft"})
    assert r.status_code == 200 and r.json() == {"success": True, "data": []}
    session.execute.assert_awaited_once()


def test_create_post(client: TestClient) -> None:
    with patch(f"{M}.create_social_post", AsyncMock(return_value={"id": "new"})) as create:
        r = client.post(BASE, json={"post_type": "manual", "text_content": "hi"})
    assert r.status_code == 200 and r.json()["data"] == {"id": "new"}
    create.assert_awaited_once()
    assert create.await_args.args[0].text_content == "hi"


@pytest.mark.parametrize(("action", "fn"), [("approve", "approve_social_post"), ("reject", "reject_social_post")])
def test_approve_reject_default_to_admin_identity(client: TestClient, action: str, fn: str) -> None:
    with patch(f"{M}.{fn}", AsyncMock()) as pipeline, patch(f"{M}.get_social_post", AsyncMock(return_value={"id": "p"})):
        r = client.post(f"{BASE}/{POST_ID}/{action}")
    assert r.status_code == 200
    pipeline.assert_awaited_once_with(POST_ID, "admin@example.com")


def test_approve_falls_back_to_user_id_without_email(client: TestClient) -> None:
    app.dependency_overrides[get_admin_user] = lambda: ADMIN.model_copy(update={"email": None})
    with patch(f"{M}.approve_social_post", AsyncMock()) as pipeline, patch(f"{M}.get_social_post", AsyncMock()):
        client.post(f"{BASE}/{POST_ID}/approve")
    pipeline.assert_awaited_once_with(POST_ID, "user_1")


def test_retry(client: TestClient) -> None:
    with patch(f"{M}.retry_social_post", AsyncMock()) as retry, patch(f"{M}.get_social_post", AsyncMock(return_value={})):
        r = client.post(f"{BASE}/{POST_ID}/retry")
    assert r.status_code == 200
    retry.assert_awaited_once_with(POST_ID)


@pytest.mark.parametrize("path", ["/v4/social", f"/v4/social/{POST_ID}", "/social", f"/v4/social/{POST_ID}/approve"])
def test_old_social_routes_gone(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404
    assert client.post(path).status_code in (404, 405)
