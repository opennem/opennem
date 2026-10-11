"""Pure ASGI maintenance gate: 503 JSON when on, pass-through when off."""

import json
from typing import Any

import pytest

from opennem import settings
from opennem.api.app import MaintenanceModeMiddleware

pytestmark = pytest.mark.asyncio


async def _run(scope_type: str = "http") -> tuple[list[dict[str, Any]], list[str]]:
    sent: list[dict[str, Any]] = []
    called: list[str] = []

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        called.append(scope["type"])

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg: dict[str, Any]) -> None:
        sent.append(msg)

    await MaintenanceModeMiddleware(inner)(
        {"type": scope_type, "method": "GET", "path": "/v4/metrics", "headers": []}, receive, send
    )
    return sent, called


async def test_maintenance_on_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", True)
    sent, called = await _run()
    assert not called
    assert sent[0]["status"] == 503
    assert json.loads(sent[1]["body"])["error"] == "Maintenance Mode"


async def test_maintenance_off_passes_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", False)
    sent, called = await _run()
    assert called == ["http"]
    assert not sent


async def test_lifespan_not_gated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", True)
    _, called = await _run("lifespan")
    assert called == ["lifespan"]
