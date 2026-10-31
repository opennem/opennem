"""Maintenance mode worker guard, start/end detection and status hook (#782)."""

import logging
from typing import Any

import pytest
from arq import cron, func
from pydantic import SecretStr

from opennem import settings
from opennem.core import maintenance as core
from opennem.tasks.maintenance import guard_jobs, maintenance_guard

pytestmark = pytest.mark.asyncio


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, Any] = {}
        self.enqueued: list[str] = []

    async def exists(self, key: str) -> int:
        return int(key in self.store)

    async def set(self, key: str, value: Any) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    async def flushdb(self) -> None:
        self.store.clear()

    async def enqueue_job(self, name: str, **kwargs: Any) -> None:
        self.enqueued.append(name)


async def _job(ctx: dict[str, Any]) -> str:
    ctx["ran"] = True
    return "done"


async def test_guard_skips_when_on(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", True)
    log = logging.getLogger("opennem.tasks.maintenance")
    log.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger="opennem.tasks.maintenance")
    try:
        ctx: dict[str, Any] = {}
        assert await maintenance_guard("cron:_job", _job)(ctx) is None
    finally:
        log.removeHandler(caplog.handler)
    assert "ran" not in ctx
    records = [r for r in caplog.records if r.name == "opennem.tasks.maintenance"]
    assert len(records) == 1
    assert records[0].levelno == logging.INFO
    assert "cron:_job" in records[0].getMessage()


async def test_guard_runs_when_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "maintenance_mode", False)
    ctx: dict[str, Any] = {}
    assert await maintenance_guard("cron:_job", _job)(ctx) == "done"
    assert ctx["ran"]


async def test_guard_reads_flag_per_call(monkeypatch: pytest.MonkeyPatch) -> None:
    guarded = maintenance_guard("cron:_job", _job)
    monkeypatch.setattr(settings, "maintenance_mode", True)
    assert await guarded({}) is None
    monkeypatch.setattr(settings, "maintenance_mode", False)
    assert await guarded({}) == "done"


def test_guard_jobs_keeps_names_and_options() -> None:
    jobs = guard_jobs([cron(_job, minute={5}, timeout=270, unique=True)])
    fns = guard_jobs([func(_job, timeout=300, max_tries=1, keep_result=0)])
    assert jobs[0].name == "cron:_job" and jobs[0].timeout_s == 270 and jobs[0].minute == {5}
    assert fns[0].name == "_job" and fns[0].max_tries == 1
    assert getattr(jobs[0].coroutine, "__name__", None) == "_job"
    # idempotent
    assert guard_jobs(jobs)[0].coroutine is jobs[0].coroutine


def test_worker_settings_all_guarded() -> None:
    from opennem.tasks.app import WorkerSettings

    for job in [*WorkerSettings.cron_jobs, *WorkerSettings.functions]:
        assert getattr(job.coroutine, "__maintenance_guarded__", False), job.name
    assert any(j.name == "cron:task_nem_interval_check" for j in WorkerSettings.cron_jobs)
    assert any(f.name == "task_sanity_webhook" for f in WorkerSettings.functions)


async def test_detect_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(settings, "maintenance_mode", True)
    assert await core.detect_transition(redis) == "maintenance.start"
    await core.set_marker(redis)
    # restart while still on: no repeat
    assert await core.detect_transition(redis) is None
    monkeypatch.setattr(settings, "maintenance_mode", False)
    assert await core.detect_transition(redis) == "maintenance.end"
    assert core.MARKER_KEY not in redis.store
    assert await core.detect_transition(redis) is None
    await core.set_marker(redis)  # no-op while off
    assert core.MARKER_KEY not in redis.store


async def test_notify_status_posts_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, Any], dict[str, str]]] = []

    async def fake_post(url: str, payload: dict[str, Any], headers: dict[str, str]) -> int:
        calls.append((url, payload, headers))
        return 204

    monkeypatch.setattr(core, "_post_json", fake_post)
    monkeypatch.setattr(settings, "slack_hook_monitoring", None)
    monkeypatch.setattr(settings, "status_webhook_url", "https://status.example.test/hook")
    monkeypatch.setattr(settings, "status_webhook_token", SecretStr("tok"))
    monkeypatch.setattr(settings, "maintenance_message", "ch upgrade")
    monkeypatch.setattr(settings, "maintenance_eta", "2026-11-02T14:00:00+10:00")

    assert await core.notify_status("maintenance.start", source="worker")
    url, payload, headers = calls[0]
    assert url == "https://status.example.test/hook"
    assert headers["Authorization"] == "Bearer tok"
    assert payload["event"] == "maintenance.start" and payload["maintenance"] is True
    assert payload["message"] == "ch upgrade" and payload["eta"] == "2026-11-02T14:00:00+10:00"
    assert payload["source"] == "worker" and payload["env"] == settings.env

    assert await core.notify_status("maintenance.end")
    assert calls[1][1]["maintenance"] is False and calls[1][1]["message"] is None


async def test_notify_status_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(*_: Any) -> int:
        raise ConnectionError("down")

    monkeypatch.setattr(core, "_post_json", boom)
    monkeypatch.setattr(settings, "slack_hook_monitoring", None)
    monkeypatch.setattr(settings, "status_webhook_url", "https://status.example.test/hook")
    assert await core.notify_status("maintenance.start") is False
    monkeypatch.setattr(settings, "status_webhook_url", None)
    assert await core.notify_status("maintenance.start") is False


async def test_startup_in_maintenance_skips_boot_work(monkeypatch: pytest.MonkeyPatch) -> None:
    import opennem.exporter.storage_bucket as storage_bucket
    import opennem.tasks.app as worker_app
    from opennem.tasks import cache_warmer

    redis = FakeRedis()
    notified: list[str] = []
    warmed: list[bool] = []

    async def fake_pool() -> FakeRedis:
        return redis

    async def fake_notify(event: str, source: str = "worker") -> bool:
        notified.append(event)
        return True

    async def fake_warm() -> None:
        warmed.append(True)

    monkeypatch.setattr(settings, "maintenance_mode", True)
    monkeypatch.setattr(worker_app, "get_redis_pool", fake_pool)
    monkeypatch.setattr(worker_app, "notify_status", fake_notify)
    monkeypatch.setattr(worker_app, "start_loop_monitor", lambda _name: None)
    monkeypatch.setattr(cache_warmer, "is_worker_mode", lambda: False)
    monkeypatch.setattr(cache_warmer, "is_enabled", lambda: True)
    monkeypatch.setattr(storage_bucket, "warm_s3_client", fake_warm)

    ctx: dict[str, Any] = {}
    await worker_app.startup(ctx)
    await ctx["maintenance_notify"]

    assert notified == ["maintenance.start"]
    assert core.MARKER_KEY in redis.store  # set after the flush
    assert redis.enqueued == []  # no cache warm queued
    assert warmed == []
