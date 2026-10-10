"""GET /milestones/instance/{instance_id} must work with and without include_history (#679)."""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from opennem.api.milestones import router as milestones_module
from opennem.api.milestones.router import milestones_router
from opennem.api.security import get_current_user
from opennem.db import get_scoped_read_session

INSTANCE_ID = uuid.UUID("01a0cbb6-e2cc-7852-8960-38e78197e4ca")


def _db_row() -> dict[str, Any]:
    return {
        "instance_id": INSTANCE_ID,
        "record_id": "au.nem.wind.power.interval.high",
        "interval": datetime(2026, 7, 1, 21, 20),
        "aggregate": "high",
        "period": "interval",
        "metric": "power",
        "network_id": "NEM",
        "network_region": None,
        "fueltech_id": "wind",
        "significance": 10,
        "value": 10349.0,
        "pct_change": 0.38,
        "value_unit": "MW",
        "description": "Interval Wind Generation high record for NEM",
        "previous_instance_id": None,
    }


async def _fake_db() -> AsyncGenerator[None]:
    yield None


async def _any_caller() -> None:
    return None


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(milestones_router, prefix="/milestones")
    app.dependency_overrides[get_scoped_read_session] = _fake_db
    app.dependency_overrides[get_current_user] = _any_caller
    return TestClient(app)


def _get(row: dict[str, Any], **params: str) -> dict[str, Any]:
    # mirrors get_milestone_record: the history key only exists when history is requested
    with patch.object(milestones_module, "get_milestone_record", AsyncMock(return_value=row)):
        resp = _client().get(f"/milestones/instance/{INSTANCE_ID}", params=params)
    assert resp.status_code == 200
    return resp.json()


def test_instance_without_history_key() -> None:
    body = _get(_db_row())
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert "history" not in body["data"][0]


def test_instance_include_history_false_ignores_history() -> None:
    body = _get({**_db_row(), "history": [_db_row()]}, include_history="false")
    assert body["success"] is True
    assert "history" not in body["data"][0]


def test_instance_include_history_true() -> None:
    body = _get({**_db_row(), "history": [_db_row()]}, include_history="true")
    assert body["success"] is True
    assert len(body["data"][0]["history"]) == 1
