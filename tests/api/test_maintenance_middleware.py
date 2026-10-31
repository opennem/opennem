"""Maintenance mode API gate and state endpoint (#782)."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from starlette.types import Message

from opennem import settings
from opennem.api.maintenance import MaintenanceModeMiddleware, is_exempt_path
from opennem.core.maintenance import DEFAULT_MESSAGE, DEFAULT_RETRY_AFTER_SECONDS, retry_after_seconds

pytestmark = pytest.mark.asyncio


@pytest.fixture
def maintenance_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", True)
    monkeypatch.setattr(settings, "maintenance_message", "upgrading the database")
    monkeypatch.setattr(settings, "maintenance_eta", "2099-01-01T00:00:00+10:00")


@pytest.fixture
def maintenance_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", False)


async def _run(path: str = "/v4/metrics", scope_type: str = "http", method: str = "GET") -> tuple[list[Message], list[str]]:
    sent: list[Message] = []
    called: list[str] = []

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        called.append(scope["type"])

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg: Message) -> None:
        sent.append(msg)

    await MaintenanceModeMiddleware(inner)({"type": scope_type, "method": method, "path": path, "headers": []}, receive, send)
    return sent, called


def _headers(msg: Message) -> dict[str, str]:
    return {k.decode(): v.decode() for k, v in msg["headers"]}


async def test_on_returns_503_with_contract(maintenance_on: None) -> None:
    sent, called = await _run()
    assert not called
    assert sent[0]["status"] == 503
    headers = _headers(sent[0])
    assert headers["content-type"] == "application/json"
    assert headers["retry-after"] == "3600"  # eta far ahead: clamped
    assert "no-store" in headers["cache-control"]
    assert "max-age" not in headers["cache-control"].replace("max-age=0", "")
    assert headers["cdn-cache-control"] == "no-store"
    assert headers["cloudflare-cdn-cache-control"] == "no-store"
    body = json.loads(sent[1]["body"])
    assert body == {
        "success": False,
        "error": "upgrading the database",
        "maintenance": True,
        "message": "upgrading the database",
        "eta": "2099-01-01T00:00:00+10:00",
    }
    assert headers["content-length"] == str(len(sent[1]["body"]))


async def test_on_head_has_no_body(maintenance_on: None) -> None:
    sent, _ = await _run(method="HEAD")
    assert sent[0]["status"] == 503
    assert sent[1]["body"] == b""


async def test_default_message_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", True)
    monkeypatch.setattr(settings, "maintenance_message", None)
    monkeypatch.setattr(settings, "maintenance_eta", None)
    sent, _ = await _run()
    body = json.loads(sent[1]["body"])
    assert body["message"] == DEFAULT_MESSAGE
    assert body["eta"] is None
    assert _headers(sent[0])["retry-after"] == str(DEFAULT_RETRY_AFTER_SECONDS)


async def test_off_passes_through(maintenance_off: None) -> None:
    sent, called = await _run()
    assert called == ["http"]
    assert not sent


async def test_lifespan_not_gated(maintenance_on: None) -> None:
    _, called = await _run(scope_type="lifespan")
    assert called == ["lifespan"]


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/health/",
        "/v4/health",
        "/v4/health/",
        "/v4/admin",
        "/maintenance",
        "/v4/maintenance",
        "/docs",
        "/v4/docs",
        "/openapi.json",
        "/v4/openapi.json",
        "/v4/admin/social",
        "/v4/admin/social/123/approve",
        "/static/x.png",
        "/robots.txt",
    ],
)
async def test_exempt_paths_pass_through(maintenance_on: None, path: str) -> None:
    assert is_exempt_path(path)
    sent, called = await _run(path=path)
    assert called == ["http"]
    assert not sent


@pytest.mark.parametrize(
    "path",
    [
        "/v4/data/network/NEM",
        "/v4/market/network/NEM",
        "/v4/facilities/",
        "/v4/me",
        "/v4/metrics",
        "/v4/healthz",
        "/v4/administrator",
    ],
)
async def test_data_paths_gated(maintenance_on: None, path: str) -> None:
    assert not is_exempt_path(path)
    sent, called = await _run(path=path)
    assert not called
    assert sent[0]["status"] == 503


def test_retry_after_from_eta(monkeypatch: pytest.MonkeyPatch) -> None:
    now = datetime(2026, 11, 1, tzinfo=UTC)
    monkeypatch.setattr(settings, "maintenance_eta", (now + timedelta(minutes=20)).isoformat())
    assert retry_after_seconds(now) == 1200
    monkeypatch.setattr(settings, "maintenance_eta", (now + timedelta(seconds=5)).isoformat())
    assert retry_after_seconds(now) == 60
    monkeypatch.setattr(settings, "maintenance_eta", (now - timedelta(minutes=5)).isoformat())
    assert retry_after_seconds(now) == DEFAULT_RETRY_AFTER_SECONDS
    monkeypatch.setattr(settings, "maintenance_eta", "2026-11-01T10:00:00")  # naive: ambiguous
    assert retry_after_seconds(now) == DEFAULT_RETRY_AFTER_SECONDS
    monkeypatch.setattr(settings, "maintenance_eta", "sunday arvo")
    assert retry_after_seconds(now) == DEFAULT_RETRY_AFTER_SECONDS


# full app: middleware order (inside CORS), real routes, no lifespan (no redis/db)


async def _client() -> httpx.AsyncClient:
    from opennem.api.app import app

    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_app_gates_data_route_with_cors(maintenance_on: None) -> None:
    async with await _client() as client:
        resp = await client.get("/v4/metrics", headers={"Origin": "https://openelectricity.org.au"})
    assert resp.status_code == 503
    assert resp.json()["maintenance"] is True
    assert resp.headers["retry-after"]
    assert "no-store" in resp.headers["cache-control"]
    # inside CORS: the browser can read the body
    assert resp.headers["access-control-allow-origin"] in ("*", "https://openelectricity.org.au")


async def test_app_health_stays_200(maintenance_on: None) -> None:
    async with await _client() as client:
        resp = await client.get("/health")
    assert resp.status_code == 200


async def test_app_maintenance_endpoint_on(maintenance_on: None) -> None:
    async with await _client() as client:
        resp = await client.get("/v4/maintenance", headers={"Origin": "https://example.com"})
    assert resp.status_code == 200
    assert resp.json() == {"maintenance": True, "message": "upgrading the database", "eta": "2099-01-01T00:00:00+10:00"}
    assert resp.headers["access-control-allow-origin"] == "*"
    assert "no-store" in resp.headers["cache-control"]
    assert resp.headers["cdn-cache-control"] == "no-store"


async def test_app_maintenance_endpoint_off(maintenance_off: None) -> None:
    async with await _client() as client:
        resp = await client.get("/v4/maintenance")
    assert resp.status_code == 200
    assert resp.json() == {"maintenance": False, "message": None, "eta": None}
    assert "no-store" in resp.headers["cache-control"]


async def test_app_off_does_not_gate(maintenance_off: None) -> None:
    async with await _client() as client:
        resp = await client.get("/v4/metrics")
    assert resp.status_code == 200
    assert "metrics" in resp.json()


async def test_maintenance_endpoint_in_openapi() -> None:
    from opennem.api.app import app

    assert "/v4/maintenance" in app.openapi()["paths"]
