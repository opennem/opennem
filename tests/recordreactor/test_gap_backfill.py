"""The multi-day gap backfill runs as its own arq job, not inside the 5-minute cron.

Since #654 a bounded backlog run seeds its running extremes from full history, so filling a gap is
minutes of ClickHouse work — a measured 482s of a 492s incremental run on dev. `task_update_milestones`
has a 300s budget, so ARQ killed the task mid-backfill, the gap stayed open, and the next tick
started it again. The incremental check now detects the gap, enqueues a job under a fixed id and
carries on with its own interval pass.
"""

from datetime import datetime

import pytest

from opennem.recordreactor import incremental
from opennem.recordreactor.incremental import GAP_BACKFILL_JOB_ID


class _FakeRedis:
    def __init__(self, job: object | None = "job-1", raises: bool = False) -> None:
        self.enqueued: list[tuple[str, str | None]] = []
        self.closed = False
        self._job = job
        self._raises = raises

    async def enqueue_job(self, function: str, *args, _job_id: str | None = None, **kwargs):
        self.enqueued.append((function, _job_id))
        if self._raises:
            raise RuntimeError("redis is down")
        return self._job

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_redis(monkeypatch):
    redis = _FakeRedis()

    async def _pool():
        return redis

    monkeypatch.setattr(incremental, "get_redis_pool", _pool)
    return redis


def _patch_gap(monkeypatch, last_milestone, now, gap_hours):
    async def _gap():
        return last_milestone, now, gap_hours

    monkeypatch.setattr(incremental, "_get_milestone_gap_hours", _gap)


def _patch_analysis(monkeypatch):
    """Capture the backlog call the job would make."""
    from opennem.recordreactor import backlog

    calls: list[dict] = []

    async def _run(**kwargs):
        calls.append(kwargs)
        return []

    monkeypatch.setattr(backlog, "run_milestone_analysis", _run)
    return calls


@pytest.mark.asyncio
async def test_gap_over_threshold_is_enqueued_not_run(monkeypatch, fake_redis) -> None:
    _patch_gap(monkeypatch, datetime(2026, 9, 21, 12, 0), datetime(2026, 9, 22, 12, 15), 24.25)
    calls = _patch_analysis(monkeypatch)

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == [("task_milestone_gap_backfill", GAP_BACKFILL_JOB_ID)]
    assert fake_redis.closed is True
    # the 5-minute cron must not carry the backlog itself
    assert calls == []


@pytest.mark.asyncio
async def test_gap_under_threshold_enqueues_nothing(monkeypatch, fake_redis) -> None:
    _patch_gap(monkeypatch, datetime(2026, 9, 22, 6, 0), datetime(2026, 9, 22, 12, 15), 6.25)

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == []


@pytest.mark.asyncio
async def test_empty_milestones_table_enqueues_nothing(monkeypatch, fake_redis) -> None:
    """An empty table needs a full rebuild, not a gap backfill."""
    _patch_gap(monkeypatch, None, datetime(2026, 9, 22, 12, 15), 0.0)

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == []


@pytest.mark.asyncio
async def test_duplicate_job_is_tolerated(monkeypatch) -> None:
    """arq returns None when the job id is already live — one backfill in flight, no exception."""
    redis = _FakeRedis(job=None)

    async def _pool():
        return redis

    monkeypatch.setattr(incremental, "get_redis_pool", _pool)
    _patch_gap(monkeypatch, datetime(2026, 9, 21, 12, 0), datetime(2026, 9, 22, 12, 15), 24.25)

    await incremental._enqueue_gap_backfill_if_needed()

    assert redis.closed is True


@pytest.mark.asyncio
async def test_enqueue_failure_does_not_break_the_incremental_pass(monkeypatch) -> None:
    """A redis problem must not take the interval detection down with it."""
    redis = _FakeRedis(raises=True)

    async def _pool():
        return redis

    monkeypatch.setattr(incremental, "get_redis_pool", _pool)
    _patch_gap(monkeypatch, datetime(2026, 9, 21, 12, 0), datetime(2026, 9, 22, 12, 15), 24.25)

    await incremental._enqueue_gap_backfill_if_needed()

    assert redis.closed is True


@pytest.mark.asyncio
async def test_job_runs_the_backlog_over_the_gap(monkeypatch) -> None:
    async def _not_in_progress(caller: str) -> bool:
        return False

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _not_in_progress)
    _patch_gap(monkeypatch, datetime(2026, 9, 21, 12, 30), datetime(2026, 9, 22, 12, 15), 24.75)
    calls = _patch_analysis(monkeypatch)

    await incremental.run_gap_backfill()

    assert len(calls) == 1
    # aligned to start of day so the day-period queries get complete days
    assert calls[0]["start_date"] == datetime(2026, 9, 21)
    assert calls[0]["end_date"] == datetime(2026, 9, 22, 12, 15)


@pytest.mark.asyncio
async def test_job_stands_down_during_a_rebuild(monkeypatch) -> None:
    """Mid-rebuild the chains are partly empty — this would insert records the rebuild wouldn't (#640)."""

    async def _in_progress(caller: str) -> bool:
        return True

    def _boom(*args, **kwargs):
        raise AssertionError("gap backfill ran during a rebuild")

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _in_progress)
    monkeypatch.setattr(incremental, "_get_milestone_gap_hours", _boom)

    await incremental.run_gap_backfill()


@pytest.mark.asyncio
async def test_job_no_ops_if_the_gap_closed_before_it_ran(monkeypatch) -> None:
    """The job re-checks: a rebuild or reconciliation may have filled the gap while it queued."""

    async def _not_in_progress(caller: str) -> bool:
        return False

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _not_in_progress)
    _patch_gap(monkeypatch, datetime(2026, 9, 22, 6, 0), datetime(2026, 9, 22, 12, 15), 6.25)
    calls = _patch_analysis(monkeypatch)

    await incremental.run_gap_backfill()

    assert calls == []
