"""#764: reprocess window after next-day dispatch, flag guard, backfill script logic. No database."""

import importlib.util
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from opennem.controllers.schema import ControllerReturn
from opennem.monitors import energy_quality_flag as guard
from opennem.workers.energy import MIN_DISPATCH_REPROCESS_WINDOW, get_dispatch_reprocess_window, reprocess_energy_window

NOW = datetime(2026, 10, 24, 12, 0)


def test_window_covers_span_of_upserted_records() -> None:
    start, end = get_dispatch_reprocess_window(datetime(2026, 10, 19, 4, 5), datetime(2026, 10, 22, 4, 0), NOW)
    assert start == datetime(2026, 10, 19, 4, 5)
    assert end == NOW


def test_window_without_span_is_at_least_four_days() -> None:
    # limit=3 files: up to 3 trading days (each starting 04:05) plus the day the first one starts in
    start, end = get_dispatch_reprocess_window(None, None, NOW)
    assert end - start >= timedelta(days=4)
    assert MIN_DISPATCH_REPROCESS_WINDOW >= timedelta(days=4)


def test_window_ignores_nonsense_future_start() -> None:
    start, _ = get_dispatch_reprocess_window(NOW + timedelta(days=1), None, NOW)
    assert start == NOW - MIN_DISPATCH_REPROCESS_WINDOW


def test_window_strips_tz() -> None:
    from datetime import UTC

    start, _ = get_dispatch_reprocess_window(datetime(2026, 10, 20, tzinfo=UTC), None, NOW)
    assert start.tzinfo is None


def test_controller_return_merges_span() -> None:
    a = ControllerReturn(interval_min=datetime(2026, 10, 20), interval_max=datetime(2026, 10, 21))
    b = ControllerReturn(interval_min=datetime(2026, 10, 19), interval_max=datetime(2026, 10, 20))
    total = ControllerReturn()
    total.merge_interval_span(a)
    total.merge_interval_span(b)
    total.merge_interval_span(ControllerReturn())
    assert (total.interval_min, total.interval_max) == (datetime(2026, 10, 19), datetime(2026, 10, 21))


@pytest.mark.asyncio
async def test_reprocess_energy_window_chunks_by_day(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[datetime, datetime]] = []

    async def fake_calc(session, start, end) -> int:
        calls.append((start, end))
        return 10

    @asynccontextmanager
    async def fake_session():
        yield MagicMock()

    monkeypatch.setattr("opennem.workers.energy._calculate_energy_for_interval", fake_calc)
    monkeypatch.setattr("opennem.workers.energy.get_write_session", fake_session)
    monkeypatch.setattr("opennem.workers.energy.settings.dry_run", False)

    rows = await reprocess_energy_window(datetime(2026, 10, 19, 4, 5), datetime(2026, 10, 22, 4, 5))
    assert len(calls) == 3
    assert rows == 30
    assert min(c[0] for c in calls) == datetime(2026, 10, 19, 4, 5)
    assert max(c[1] for c in calls) == datetime(2026, 10, 22, 4, 5)


# guard


def test_guard_threshold_is_strictly_above() -> None:
    assert not guard.exceeds_threshold(500, 500)
    assert guard.exceeds_threshold(501, 500)
    assert not guard.exceeds_threshold(0, 500)


def test_guard_window_bounds() -> None:
    start, end = guard.get_check_window(NOW)
    assert end == NOW - timedelta(days=3)
    assert start == NOW - timedelta(days=14)


def _stub_session(rows: list[tuple[datetime, int]]):
    result = MagicMock()
    result.all.return_value = rows
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    @asynccontextmanager
    async def ctx():
        yield session

    return ctx, session


@pytest.mark.asyncio
async def test_guard_alerts_above_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, session = _stub_session([(datetime(2026, 10, 14), 184320), (datetime(2026, 10, 15), 184320)])
    monkeypatch.setattr(guard, "get_read_session", ctx)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_enabled", True)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_threshold", 500)
    sentry = MagicMock()
    monkeypatch.setattr(guard.sentry_sdk, "new_scope", sentry)

    result = await guard.run_energy_quality_flag_check(now=NOW)

    assert result is not None and result.total == 368640
    assert result.by_day == {"2026-10-14": 184320, "2026-10-15": 184320}
    scope = sentry.return_value.__enter__.return_value
    scope.capture_message.assert_called_once()
    params = session.execute.await_args.args[1]
    assert params["window_end"] == NOW - timedelta(days=3)


@pytest.mark.asyncio
async def test_guard_quiet_at_or_below_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, _ = _stub_session([(datetime(2026, 10, 14), 12)])
    monkeypatch.setattr(guard, "get_read_session", ctx)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_enabled", True)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_threshold", 500)
    sentry = MagicMock()
    monkeypatch.setattr(guard.sentry_sdk, "new_scope", sentry)

    result = await guard.run_energy_quality_flag_check(now=NOW)

    assert result is not None and result.total == 12
    sentry.assert_not_called()


@pytest.mark.asyncio
async def test_guard_disabled_skips_query(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, session = _stub_session([])
    monkeypatch.setattr(guard, "get_read_session", ctx)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_enabled", False)

    assert await guard.run_energy_quality_flag_check(now=NOW) is None
    session.execute.assert_not_awaited()


# backfill script

_SPEC = importlib.util.spec_from_file_location("energy_backfill", Path(__file__).parents[2] / "bin" / "energy_backfill.py")
assert _SPEC and _SPEC.loader
backfill = importlib.util.module_from_spec(_SPEC)
sys.modules["energy_backfill"] = backfill
_SPEC.loader.exec_module(backfill)


def test_backfill_chunks_default_three_days() -> None:
    chunks = backfill.plan_chunks(datetime(2026, 3, 24), datetime(2026, 4, 1), 3)
    assert chunks[0] == (datetime(2026, 3, 24), datetime(2026, 3, 27))
    assert chunks[-1][1] == datetime(2026, 4, 1)
    assert len(chunks) == 3


def test_backfill_defaults_dry_run_and_two_workers() -> None:
    args = backfill.parse_args(["--start", "2026-03-24", "--end", "2026-03-30"])
    assert args.apply is False and args.max_workers == 2 and args.chunk_days == 3


def test_backfill_refuses_prod_without_flag() -> None:
    args = backfill.parse_args(["--start", "2026-03-24", "--end", "2026-03-30", "--apply"])
    assert backfill.check_write_allowed(args, "db-prod.example.com")
    assert backfill.check_write_allowed(args, "db-dev.example.com") is None
    ok = backfill.parse_args(["--start", "2026-03-24", "--end", "2026-03-30", "--apply", "--i-know-this-writes"])
    assert backfill.check_write_allowed(ok, "db-prod.example.com") is None


def test_backfill_dry_run_never_refuses() -> None:
    args = backfill.parse_args(["--start", "2026-03-24", "--end", "2026-03-30"])
    assert backfill.check_write_allowed(args, "db-prod.example.com") is None


def test_backfill_target_has_no_credentials() -> None:
    host, db = backfill.describe_target("postgresql+asyncpg://user:s3cret@db-prod.example.com:5432/opennem")
    assert (host, db) == ("db-prod.example.com", "opennem")
    assert "s3cret" not in f"{host}{db}"


def test_backfill_validate() -> None:
    bad = backfill.parse_args(["--start", "2026-03-30", "--end", "2026-03-24"])
    assert backfill.validate(bad)


# task wiring


@pytest.mark.asyncio
async def test_per_day_task_reprocesses_crawled_span_with_limit_3(monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.tasks import tasks

    crawl_calls: list[dict[str, Any]] = []

    async def fake_run_crawl(crawler, **kwargs):
        crawl_calls.append({"name": crawler.name, **kwargs})
        if crawler.name == tasks.AEMONEMNextDayDispatch.name:
            return ControllerReturn(
                inserted_records=5, interval_min=datetime(2026, 10, 20, 4, 5), interval_max=datetime(2026, 10, 23, 4, 0)
            )
        return ControllerReturn(inserted_records=5)

    reprocess = AsyncMock()
    monkeypatch.setattr(tasks, "run_crawl", fake_run_crawl)
    monkeypatch.setattr(tasks, "reprocess_energy_window", reprocess)
    monkeypatch.setattr(tasks, "get_last_completed_interval_for_network", lambda **_: NOW)

    await tasks.task_nem_per_day_check({"job_try": 1})

    assert all(c["limit"] == 3 for c in crawl_calls)
    reprocess.assert_awaited_once_with(date_start=datetime(2026, 10, 20, 4, 5), date_end=NOW)


@pytest.mark.asyncio
async def test_per_day_task_retry_semantics_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    from arq import Retry

    from opennem.tasks import tasks

    async def fake_run_crawl(crawler, **kwargs):
        return ControllerReturn(inserted_records=0)

    reprocess = AsyncMock()
    monkeypatch.setattr(tasks, "run_crawl", fake_run_crawl)
    monkeypatch.setattr(tasks, "reprocess_energy_window", reprocess)

    with pytest.raises(Retry):
        await tasks.task_nem_per_day_check({"job_try": 2})
    reprocess.assert_not_awaited()
