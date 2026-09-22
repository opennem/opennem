"""The gap backfill runs as its own arq job, keyed off a watermark of the last completed pass.

Since #654 a bounded backlog run seeds its running extremes from full history, so filling a gap is
minutes of ClickHouse work — a measured 482s of a 492s incremental run on dev. `task_update_milestones`
has a 300s budget, so ARQ killed the task mid-backfill, the gap stayed open, and the next tick
started it again. The incremental check now detects the gap, enqueues a job under a fixed id and
carries on with its own interval pass.

Staleness is measured against the watermark, not `max(milestones.interval)`. Measuring the newest
record meant a healthy system — which routinely goes more than a day without setting one — never
closed the gap, and the job re-enqueued itself every 15 minutes indefinitely (#658).
"""

from datetime import datetime, timedelta

import pytest

from opennem import settings
from opennem.recordreactor import incremental
from opennem.recordreactor.incremental import GAP_BACKFILL_JOB_ID

NOW = datetime(2026, 9, 22, 14, 10)
THRESHOLD_HOURS = 3


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


@pytest.fixture(autouse=True)
def threshold(monkeypatch):
    monkeypatch.setattr(settings, "milestone_gap_backfill_threshold_hours", THRESHOLD_HOURS)


@pytest.fixture(autouse=True)
def table_has_milestones(monkeypatch):
    """Default: the table is populated. The empty-table tests override this."""

    async def _not_empty():
        return False

    monkeypatch.setattr(incremental, "_milestones_table_is_empty", _not_empty)


@pytest.fixture(autouse=True)
def no_recent_enqueue(monkeypatch):
    """Default: no backfill queued recently, and record what the detector writes."""
    written: list[datetime] = []

    async def _get():
        return None

    async def _set(when):
        written.append(when)

    monkeypatch.setattr(incremental, "get_gap_backfill_enqueued_at", _get)
    monkeypatch.setattr(incremental, "set_gap_backfill_enqueued_at", _set)
    return written


def _patch_watermark(monkeypatch, watermark: datetime | None, now: datetime = NOW):
    """The checker last completed a pass at `watermark` (None = never)."""

    async def _get():
        return watermark

    monkeypatch.setattr(incremental, "get_last_incremental_run", _get)
    monkeypatch.setattr(incremental, "get_last_completed_interval_for_network", lambda *a, **k: now)


def _patch_empty_table(monkeypatch):
    async def _empty():
        return True

    monkeypatch.setattr(incremental, "_milestones_table_is_empty", _empty)


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
async def test_downtime_over_threshold_is_enqueued_not_run(monkeypatch, fake_redis, no_recent_enqueue) -> None:
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))
    calls = _patch_analysis(monkeypatch)

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == [("task_milestone_gap_backfill", GAP_BACKFILL_JOB_ID)]
    assert fake_redis.closed is True
    # the 5-minute cron must not carry the backlog itself
    assert calls == []
    # and the enqueue is remembered so the next tick doesn't queue another
    assert no_recent_enqueue == [NOW]


@pytest.mark.asyncio
async def test_a_recent_pass_enqueues_nothing(monkeypatch, fake_redis) -> None:
    _patch_watermark(monkeypatch, NOW - timedelta(minutes=5))

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == []


@pytest.mark.asyncio
async def test_downtime_is_measured_from_the_watermark(monkeypatch) -> None:
    """#658: dev looped every 15 minutes because the newest record was 26h old and legitimately so.

    The checker had completed a pass seconds earlier and was correctly writing nothing. Staleness
    is the age of that pass, whatever the newest record says.
    """
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))

    watermark, now, hours = await incremental._get_downtime_hours()

    assert watermark == NOW - timedelta(hours=26)
    assert now == NOW
    assert hours == pytest.approx(26.0)


@pytest.mark.asyncio
async def test_no_watermark_reports_no_downtime(monkeypatch) -> None:
    _patch_watermark(monkeypatch, None)

    watermark, _, hours = await incremental._get_downtime_hours()

    assert watermark is None
    assert hours == 0.0


@pytest.mark.asyncio
async def test_empty_milestones_table_enqueues_nothing(monkeypatch, fake_redis) -> None:
    """An empty table needs a full rebuild, not a gap backfill."""
    _patch_empty_table(monkeypatch)
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == []


@pytest.mark.asyncio
async def test_missing_watermark_enqueues_nothing(monkeypatch, fake_redis) -> None:
    """Fresh deployment: no evidence of downtime, and this run will record one."""
    _patch_watermark(monkeypatch, None)

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == []


@pytest.mark.asyncio
async def test_cooldown_holds_off_a_second_enqueue(monkeypatch, fake_redis) -> None:
    """A pass that keeps failing before it updates the watermark must not queue a job every tick."""
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))

    async def _enqueued_recently():
        return NOW - timedelta(minutes=10)

    monkeypatch.setattr(incremental, "get_gap_backfill_enqueued_at", _enqueued_recently)

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == []


@pytest.mark.asyncio
async def test_cooldown_expires(monkeypatch, fake_redis) -> None:
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))

    async def _enqueued_long_ago():
        return NOW - incremental.GAP_BACKFILL_COOLDOWN - timedelta(minutes=1)

    monkeypatch.setattr(incremental, "get_gap_backfill_enqueued_at", _enqueued_long_ago)

    await incremental._enqueue_gap_backfill_if_needed()

    assert fake_redis.enqueued == [("task_milestone_gap_backfill", GAP_BACKFILL_JOB_ID)]


@pytest.mark.asyncio
async def test_duplicate_job_is_tolerated(monkeypatch) -> None:
    """arq returns None when the job id is already live — one backfill in flight, no exception."""
    redis = _FakeRedis(job=None)

    async def _pool():
        return redis

    monkeypatch.setattr(incremental, "get_redis_pool", _pool)
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))

    await incremental._enqueue_gap_backfill_if_needed()

    assert redis.closed is True


@pytest.mark.asyncio
async def test_enqueue_failure_does_not_break_the_incremental_pass(monkeypatch) -> None:
    """A redis problem must not take the interval detection down with it."""
    redis = _FakeRedis(raises=True)

    async def _pool():
        return redis

    monkeypatch.setattr(incremental, "get_redis_pool", _pool)
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))

    await incremental._enqueue_gap_backfill_if_needed()

    assert redis.closed is True


@pytest.mark.asyncio
async def test_job_runs_the_backlog_over_the_missed_window(monkeypatch) -> None:
    async def _not_in_progress(caller: str) -> bool:
        return False

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _not_in_progress)
    _patch_watermark(monkeypatch, datetime(2026, 9, 21, 12, 30))
    calls = _patch_analysis(monkeypatch)

    await incremental.run_gap_backfill()

    assert len(calls) == 1
    # from the watermark, aligned to start of day so the day-period queries get complete days
    assert calls[0]["start_date"] == datetime(2026, 9, 21)
    assert calls[0]["end_date"] == NOW


@pytest.mark.asyncio
async def test_job_stands_down_during_a_rebuild(monkeypatch) -> None:
    """Mid-rebuild the chains are partly empty — this would insert records the rebuild wouldn't (#640)."""

    async def _in_progress(caller: str) -> bool:
        return True

    def _boom(*args, **kwargs):
        raise AssertionError("gap backfill ran during a rebuild")

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _in_progress)
    monkeypatch.setattr(incremental, "_milestones_table_is_empty", _boom)

    await incremental.run_gap_backfill()


@pytest.mark.asyncio
async def test_job_no_ops_if_the_checker_caught_up_before_it_ran(monkeypatch) -> None:
    """The job re-checks: the checker may have completed a pass while the job queued."""

    async def _not_in_progress(caller: str) -> bool:
        return False

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _not_in_progress)
    _patch_watermark(monkeypatch, NOW - timedelta(minutes=5))
    calls = _patch_analysis(monkeypatch)

    await incremental.run_gap_backfill()

    assert calls == []


@pytest.mark.asyncio
async def test_job_no_ops_on_an_empty_table(monkeypatch) -> None:
    async def _not_in_progress(caller: str) -> bool:
        return False

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _not_in_progress)
    _patch_empty_table(monkeypatch)
    _patch_watermark(monkeypatch, NOW - timedelta(hours=26))
    calls = _patch_analysis(monkeypatch)

    await incremental.run_gap_backfill()

    assert calls == []


@pytest.mark.asyncio
async def test_a_pass_that_finds_nothing_still_records_the_watermark(monkeypatch) -> None:
    """The #658 condition exactly: a healthy system writing no records must still look alive."""
    written: list[datetime] = []

    async def _no_rebuild(caller: str) -> bool:
        return False

    async def _no_gap() -> None:
        return None

    async def _no_state() -> dict:
        return {}

    async def _record(when: datetime) -> None:
        written.append(when)

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _no_rebuild)
    monkeypatch.setattr(incremental, "_enqueue_gap_backfill_if_needed", _no_gap)
    monkeypatch.setattr(incremental, "get_clickhouse_client", lambda: object())
    monkeypatch.setattr(incremental, "refresh_current_milestone_state", _no_state)
    monkeypatch.setattr(incremental, "get_last_settled_interval", lambda **kwargs: NOW)
    monkeypatch.setattr(incremental, "query_all_groupings_for_period", lambda **kwargs: [])
    monkeypatch.setattr(incremental, "get_last_completed_interval_for_network", lambda *a, **k: NOW)
    monkeypatch.setattr(incremental, "set_last_incremental_run", _record)

    assert await incremental.run_incremental_milestone_check(alert_slack=False) == []

    assert written == [NOW]


@pytest.mark.asyncio
async def test_a_stood_down_run_does_not_record_the_watermark(monkeypatch) -> None:
    """Standing down for a rebuild is not a completed pass."""

    async def _in_progress(caller: str) -> bool:
        return True

    def _boom(*args, **kwargs):
        raise AssertionError("a stood-down run must not touch the watermark")

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _in_progress)
    monkeypatch.setattr(incremental, "set_last_incremental_run", _boom)

    assert await incremental.run_incremental_milestone_check(alert_slack=False) == []
