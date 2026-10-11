"""/metrics response matches the golden captured from dev before the constant refactor"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opennem.api import app as app_module
from opennem.api.app import get_metrics

GOLDEN = json.loads((Path(__file__).parent.parent / "fixtures" / "metrics_golden.json").read_text())


@pytest.mark.asyncio
async def test_metrics_equals_golden() -> None:
    resp = await get_metrics()
    assert resp.media_type == "application/json"
    assert json.loads(resp.body) == GOLDEN


@pytest.mark.asyncio
async def test_metrics_body_is_shared_bytes() -> None:
    """Immutable pre-encoded body: callers cannot mutate shared state."""
    assert isinstance(app_module._METRICS_BODY, bytes)
    assert (await get_metrics()).body is app_module._METRICS_BODY


def test_metrics_is_precomputed() -> None:
    assert hasattr(app_module, "_METRICS_RESPONSE")


def test_metrics_http_ok() -> None:
    resp = TestClient(app_module.app).get("/v4/metrics")
    assert resp.status_code in (200, 401, 403)
    if resp.status_code == 200:
        assert resp.json() == GOLDEN
