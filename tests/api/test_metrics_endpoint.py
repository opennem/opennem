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
    assert await get_metrics() == GOLDEN


@pytest.mark.asyncio
async def test_metrics_mutation_does_not_leak() -> None:
    first = await get_metrics()
    first["metrics"].clear()
    first["endpoints"]["market"].append("x")
    assert await get_metrics() == GOLDEN


def test_metrics_is_precomputed() -> None:
    assert hasattr(app_module, "_METRICS_RESPONSE")


def test_metrics_http_ok() -> None:
    resp = TestClient(app_module.app).get("/v4/metrics")
    assert resp.status_code in (200, 401, 403)
