"""#786: daily milestone head audit monitor. Alert only, deduped, stands down during a rebuild."""

from datetime import datetime
from typing import Any

import pytest

from opennem.monitors import milestone_head_audit as monitor
from opennem.recordreactor.head_audit import AuditStatus, HeadFinding


def _finding(record_id: str, status: AuditStatus = AuditStatus.bad) -> HeadFinding:
    return HeadFinding(
        record_id=record_id,
        interval=datetime(2026, 10, 1),
        period="month",
        aggregate="high",
        significance=9,
        network_id="NEM",
        status=status,
        stored=124_943,
        recomputed=124_943,
        best_interval=datetime(2026, 8, 1),
        best_value=125_160,
        reason="beaten by earlier 2026-08-01 125,160",
    )


class _FakeRedis:
    store: dict[str, Any] = {}

    async def get(self, key: str) -> Any:
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value.encode()

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    async def close(self) -> None:
        return None


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    state: dict[str, Any] = {"findings": [], "slack": [], "sentry": [], "rebuild": False, "slack_ok": True}
    _FakeRedis.store = {}

    async def fake_audit_heads(**_: Any) -> list[HeadFinding]:
        return state["findings"]

    async def fake_skip(caller: str) -> bool:
        return state["rebuild"]

    async def fake_slack(**kwargs: Any) -> bool:
        state["slack"].append(kwargs["message"])
        return state["slack_ok"]

    async def fake_pool() -> _FakeRedis:
        return _FakeRedis()

    class _Scope:
        fingerprint: list[str] = []

        def __enter__(self) -> "_Scope":
            return self

        def __exit__(self, *_: Any) -> None:
            return None

        def set_tag(self, *_: Any) -> None:
            return None

        def set_context(self, *_: Any) -> None:
            return None

        def capture_message(self, message: str, level: str) -> None:
            state["sentry"].append((self.fingerprint, message, level))

    monkeypatch.setattr(monitor, "audit_heads", fake_audit_heads)
    monkeypatch.setattr("opennem.recordreactor.rebuild_guard.skip_if_rebuild_in_progress", fake_skip)
    monkeypatch.setattr("opennem.clients.slack.slack_message", fake_slack)
    monkeypatch.setattr("opennem.tasks.broker.get_redis_pool", fake_pool)
    monkeypatch.setattr(monitor.sentry_sdk, "new_scope", lambda: _Scope())
    return state


@pytest.mark.asyncio
async def test_clean_audit_sends_nothing(wired: dict[str, Any]) -> None:
    wired["findings"] = [_finding("a", AuditStatus.ok), _finding("b", AuditStatus.suspect)]
    assert await monitor.run_milestone_head_audit_check() == []
    assert wired["slack"] == [] and wired["sentry"] == []


@pytest.mark.asyncio
async def test_bad_heads_alert_once_per_set(wired: dict[str, Any]) -> None:
    wired["findings"] = [_finding("au.nem.vic1.battery_discharging.energy.month.high")]

    bad = await monitor.run_milestone_head_audit_check()
    assert [f.record_id for f in bad] == ["au.nem.vic1.battery_discharging.energy.month.high"]
    assert len(wired["slack"]) == 1
    assert "au.nem.vic1.battery_discharging.energy.month.high" in wired["slack"][0]
    assert wired["sentry"][0][0] == ["milestone-head-audit-bad"]
    assert wired["sentry"][0][2] == "warning"

    # same BAD set next day: sentry groups it, slack stays quiet
    await monitor.run_milestone_head_audit_check()
    assert len(wired["slack"]) == 1
    assert len(wired["sentry"]) == 2

    # a new BAD head changes the set: post again
    wired["findings"] = [*wired["findings"], _finding("au.nem.battery_charging.energy.month.high")]
    await monitor.run_milestone_head_audit_check()
    assert len(wired["slack"]) == 2


@pytest.mark.asyncio
async def test_stands_down_during_rebuild(wired: dict[str, Any]) -> None:
    wired["rebuild"] = True
    wired["findings"] = [_finding("x")]
    assert await monitor.run_milestone_head_audit_check() == []
    assert wired["slack"] == [] and wired["sentry"] == []


def test_bad_digest_is_order_independent_and_ignores_non_bad() -> None:
    a, b = _finding("a"), _finding("b")
    ok = _finding("c", AuditStatus.ok)
    assert monitor.bad_digest([a, b]) == monitor.bad_digest([b, ok, a])
    assert monitor.bad_digest([a]) != monitor.bad_digest([a, b])


@pytest.mark.asyncio
async def test_failed_post_is_retried_and_clean_run_resets(wired: dict[str, Any]) -> None:
    wired["findings"] = [_finding("a")]
    wired["slack_ok"] = False
    await monitor.run_milestone_head_audit_check()
    wired["slack_ok"] = True
    await monitor.run_milestone_head_audit_check()
    assert len(wired["slack"]) == 2  # the failed post did not mute the set

    wired["findings"] = []
    await monitor.run_milestone_head_audit_check()
    wired["findings"] = [_finding("a")]
    await monitor.run_milestone_head_audit_check()
    assert len(wired["slack"]) == 3  # fixed then back: news again
