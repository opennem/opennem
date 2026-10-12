"""Sanity webhook enqueues a deferred ARQ job and returns immediately"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opennem import settings
from opennem.api.webhooks import router as webhook_router

SECRET = "test-secret"
PROJECT_ID = "proj123"
HEADERS = {"Content-Type": "application/json", "sanity-project-id": PROJECT_ID}
PAYLOAD = {"_type": "facility", "_id": "abc"}


@pytest.fixture
def redis(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    monkeypatch.setattr(settings, "webhook_secret", SECRET)
    monkeypatch.setattr(settings, "sanity_project_id", PROJECT_ID)

    pool = MagicMock()
    pool.enqueue_job = AsyncMock(return_value=MagicMock())
    pool.close = AsyncMock()
    monkeypatch.setattr(webhook_router, "get_redis_pool", AsyncMock(return_value=pool), raising=False)
    return pool


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(webhook_router.router)
    return TestClient(app)


def test_enqueues_deferred_job_and_returns_ok(client: TestClient, redis: MagicMock) -> None:
    resp = client.post(f"/sanity/{SECRET}", json=PAYLOAD, headers=HEADERS)

    assert resp.status_code == 200
    assert resp.json() == "OK"
    redis.enqueue_job.assert_awaited_once()
    args, kwargs = redis.enqueue_job.await_args
    assert args[0] == "task_sanity_webhook"
    assert args[1:] == ("facility", "abc")
    assert kwargs["_defer_by"] == 60
    assert kwargs["_job_id"] == "sanity:facility:abc"


def test_type_is_lowercased_and_id_stripped_in_job_id(client: TestClient, redis: MagicMock) -> None:
    resp = client.post(f"/sanity/{SECRET}", json={"_type": "Unit", "_id": " u1 "}, headers=HEADERS)

    assert resp.status_code == 200
    _, kwargs = redis.enqueue_job.await_args
    assert kwargs["_job_id"] == "sanity:unit:u1"


def test_duplicate_enqueue_is_deduped_and_still_ok(client: TestClient, redis: MagicMock) -> None:
    # arq returns None when a job with the same _job_id is already queued
    redis.enqueue_job.side_effect = [MagicMock(), None]

    first = client.post(f"/sanity/{SECRET}", json=PAYLOAD, headers=HEADERS)
    second = client.post(f"/sanity/{SECRET}", json=PAYLOAD, headers=HEADERS)

    assert first.status_code == second.status_code == 200
    assert second.json() == "OK"
    ids = [c.kwargs["_job_id"] for c in redis.enqueue_job.await_args_list]
    assert ids == ["sanity:facility:abc"] * 2


def test_bad_secret_404(client: TestClient, redis: MagicMock) -> None:
    resp = client.post("/sanity/nope", json=PAYLOAD, headers=HEADERS)
    assert resp.status_code == 404
    redis.enqueue_job.assert_not_awaited()


def test_missing_content_type_400(client: TestClient, redis: MagicMock) -> None:
    resp = client.post(f"/sanity/{SECRET}", content=b"{}", headers={"sanity-project-id": PROJECT_ID})
    assert resp.status_code == 400
    redis.enqueue_job.assert_not_awaited()


def test_wrong_project_id_400(client: TestClient, redis: MagicMock) -> None:
    resp = client.post(f"/sanity/{SECRET}", json=PAYLOAD, headers={**HEADERS, "sanity-project-id": "other"})
    assert resp.status_code == 400
    redis.enqueue_job.assert_not_awaited()


def test_missing_project_id_400(client: TestClient, redis: MagicMock) -> None:
    resp = client.post(f"/sanity/{SECRET}", json=PAYLOAD, headers={"Content-Type": "application/json"})
    assert resp.status_code == 400


@pytest.mark.parametrize("payload", [{"_id": "abc"}, {"_type": "facility"}])
def test_missing_fields_400(client: TestClient, redis: MagicMock, payload: dict) -> None:
    resp = client.post(f"/sanity/{SECRET}", json=payload, headers=HEADERS)
    assert resp.status_code == 400
    redis.enqueue_job.assert_not_awaited()


def test_enqueue_failure_503(client: TestClient, redis: MagicMock) -> None:
    # sanity retries on 5xx, so a redis outage must not silently drop the edit
    redis.enqueue_job.side_effect = ConnectionError("redis down")
    resp = client.post(f"/sanity/{SECRET}", json=PAYLOAD, headers=HEADERS)
    assert resp.status_code == 503
