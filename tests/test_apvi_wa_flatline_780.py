"""#780: APVI WA rooftop flat line across a truncated source day.

APVI returned 17 WA intervals for 2024-11-25 and the unit_intervals rooftop CTE locf()'d the
last one ~30h. Covers the staleness cap on the carry-forward (both query builders), the 7-day
APVI re-fetch and its changed-day re-aggregation, and the alert-only truncation check.
No database: SQL is asserted at source level like test_rooftop_fill_forward.py.
"""

import inspect
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from opennem.aggregates import unit_intervals
from opennem.aggregates.unit_intervals import (
    _ROOFTOP_DUSK_FROM,
    _ROOFTOP_DUSK_MAX_MW,
    _ROOFTOP_KEEP_SQL,
    _ROOFTOP_MAX_STALENESS,
    _ROOFTOP_STALE_SQL,
    _get_unit_interval_data,
    _stream_unit_interval_data,
)
from opennem.monitors import apvi_truncation as check
from opennem.workers import apvi_latest

# --- staleness cap ----------------------------------------------------------


def _collapse(fn) -> str:
    return " ".join(inspect.getsource(fn).split())


def _rendered_sql(fn) -> str:
    """The f-string SQL with the module constants substituted, whitespace collapsed."""
    src = _collapse(fn)
    for name in ("_ROOFTOP_KEEP_SQL", "_ROOFTOP_STALE_SQL", "_ROOFTOP_STALENESS_SQL"):
        src = src.replace("{" + name + "}", getattr(unit_intervals, name))
    return src


def test_staleness_is_one_hour_and_wider_than_trailing_bound() -> None:
    assert _ROOFTOP_MAX_STALENESS == timedelta(hours=1)
    # the trailing edge (+25 min past the last real reading) must never trip the cap,
    # so the #579 catch-up behaviour at the bleeding edge is unchanged
    assert _ROOFTOP_MAX_STALENESS > timedelta(minutes=25)
    assert "interval '60 minutes'" in _ROOFTOP_STALE_SQL


@pytest.mark.parametrize("fn", [_get_unit_interval_data, _stream_unit_interval_data])
def test_both_builders_track_last_real_reading(fn) -> None:
    src = _collapse(fn)
    assert "locf(max(fs.interval)) as last_real_interval" in src, f"{fn.__name__}: needs per-bucket last real reading"


@pytest.mark.parametrize("fn", [_get_unit_interval_data, _stream_unit_interval_data])
def test_both_builders_apply_cap(fn) -> None:
    src = _rendered_sql(fn)
    # the #579 trailing bound is kept as is
    assert "interval <= max_real_interval + interval '25 minutes'" in src
    # stale buckets are filtered, and the ones kept read 0
    assert f"AND {_ROOFTOP_KEEP_SQL}" in src
    assert f"CASE WHEN {_ROOFTOP_STALE_SQL} THEN 0 ELSE generated END as generated" in src
    assert f"CASE WHEN {_ROOFTOP_STALE_SQL} THEN 0 ELSE energy END as energy" in src


def test_keep_rule_preserves_night_zero_and_dusk_tail() -> None:
    # fresh, carried 0 (APVI publishes daylight only, nights are a carried 0), small dusk tail
    assert _ROOFTOP_KEEP_SQL.startswith(f"(NOT ({_ROOFTOP_STALE_SQL}) OR generated = 0 ")
    assert f"CAST(last_real_interval AS time) >= time '{_ROOFTOP_DUSK_FROM}'" in _ROOFTOP_KEEP_SQL
    assert f"generated < {_ROOFTOP_DUSK_MAX_MW}" in _ROOFTOP_KEEP_SQL
    # the truncation alert threshold sits above the dusk tail ceiling, so a flagged day is never zero-filled
    assert check.TRUNCATED_MIN_MW > _ROOFTOP_DUSK_MAX_MW
    assert time.fromisoformat(_ROOFTOP_DUSK_FROM) == check.TRUNCATED_BEFORE


def _keep(interval: datetime, last_real: datetime, carried: float) -> tuple[bool, float]:
    """Python model of the SQL keep/zero rule, used to pin the intended outcomes."""
    stale = interval >= last_real + _ROOFTOP_MAX_STALENESS
    keep = (
        not stale
        or carried == 0
        or (last_real.time() >= time.fromisoformat(_ROOFTOP_DUSK_FROM) and carried < _ROOFTOP_DUSK_MAX_MW)
    )
    return keep, 0.0 if stale else carried


def test_model_truncated_day_goes_null_after_an_hour() -> None:
    last = datetime(2024, 11, 25, 10, 30)
    assert _keep(last + timedelta(minutes=55), last, 1075.6) == (True, 1075.6)
    assert _keep(last + timedelta(hours=1), last, 1075.6)[0] is False
    assert _keep(last + timedelta(hours=20), last, 1075.6)[0] is False


def test_model_night_and_dusk() -> None:
    dusk = datetime(2023, 2, 4, 19, 15)
    assert _keep(dusk + timedelta(hours=3), dusk, 29.7) == (True, 0.0)
    night = datetime(2026, 10, 20, 19, 30)
    assert _keep(night + timedelta(hours=8), night, 0.0) == (True, 0.0)
    # a missed 30-min AEMO block mid-day is still bridged
    noon = datetime(2026, 10, 20, 12, 0)
    assert _keep(noon + timedelta(minutes=50), noon, 2000.0) == (True, 2000.0)


# --- apvi.latest.data refresh -----------------------------------------------


def test_changed_days() -> None:
    before = {date(2026, 10, 27): (70, 1.0), date(2026, 10, 28): (13, 2.0)}
    after = {date(2026, 10, 27): (70, 1.0), date(2026, 10, 28): (62, 9.0), date(2026, 10, 29): (5, 1.0)}
    assert apvi_latest.changed_days(before, after) == [date(2026, 10, 28), date(2026, 10, 29)]
    assert apvi_latest.changed_days(before, dict(before)) == []


def test_reaggregate_window() -> None:
    now = datetime(2026, 10, 31, 9, 0)
    assert apvi_latest.reaggregate_window([], now) is None
    # next day included so night buckets bounded by the next morning are rebuilt
    assert apvi_latest.reaggregate_window([date(2026, 10, 25), date(2026, 10, 28)], now) == (
        datetime(2026, 10, 25),
        datetime(2026, 10, 30),
    )
    # never past now
    assert apvi_latest.reaggregate_window([date(2026, 10, 31)], now) == (datetime(2026, 10, 31), now)


@pytest.mark.asyncio
async def test_refresh_reaggregates_only_changed_days(monkeypatch: pytest.MonkeyPatch) -> None:
    fingerprints = iter([{date(2026, 10, 28): (13, 2.0)}, {date(2026, 10, 28): (62, 9.0)}])
    monkeypatch.setattr(apvi_latest, "_fingerprint", AsyncMock(side_effect=lambda _start: next(fingerprints)))
    crawl = AsyncMock()
    monkeypatch.setattr(apvi_latest, "run_crawl", crawl)
    backlog = AsyncMock()
    monkeypatch.setattr(apvi_latest, "process_unit_intervals_backlog", backlog)

    @asynccontextmanager
    async def fake_session():
        yield MagicMock()

    monkeypatch.setattr(apvi_latest, "get_write_session", fake_session)

    result = await apvi_latest.run_apvi_latest_refresh(now=datetime(2026, 10, 31, 9, 0))

    crawl.assert_awaited_once_with(apvi_latest.APVIRooftopLatestCrawler)
    assert result.changed_days == [date(2026, 10, 28)]
    assert backlog.await_args is not None
    kwargs = backlog.await_args.kwargs
    assert (kwargs["start_date"], kwargs["end_date"]) == (datetime(2026, 10, 28), datetime(2026, 10, 30))
    assert kwargs["network"].code == "APVI"


@pytest.mark.asyncio
async def test_refresh_skips_aggregate_when_nothing_changed(monkeypatch: pytest.MonkeyPatch) -> None:
    same = {date(2026, 10, 28): (62, 9.0)}
    monkeypatch.setattr(apvi_latest, "_fingerprint", AsyncMock(return_value=same))
    monkeypatch.setattr(apvi_latest, "run_crawl", AsyncMock())
    backlog = AsyncMock()
    monkeypatch.setattr(apvi_latest, "process_unit_intervals_backlog", backlog)

    result = await apvi_latest.run_apvi_latest_refresh(now=datetime(2026, 10, 31, 9, 0))

    assert result.window is None
    backlog.assert_not_awaited()


def test_latest_crawler_is_seven_day_lookback() -> None:
    crawler = apvi_latest.APVIRooftopLatestCrawler
    assert crawler.name == "apvi.latest.data"
    assert crawler.limit == 7
    assert crawler.latest is False


def test_tasks_are_scheduled() -> None:
    from opennem.tasks.app import WorkerSettings

    names = {getattr(job.coroutine, "__name__", "") for job in WorkerSettings.cron_jobs}
    assert {"task_apvi_latest_crawl", "task_check_apvi_truncation"} <= names


# --- truncation check -------------------------------------------------------

NOW = datetime(2026, 10, 31, 8, 0)


def test_is_truncated() -> None:
    assert check.is_truncated(datetime(2024, 11, 25, 10, 30), 1075.6)
    assert check.is_truncated(datetime(2023, 11, 22, 8, 0), 912.7)
    # normal dusk end
    assert not check.is_truncated(datetime(2026, 10, 20, 19, 30), 0.0)
    # small value mid-day (cloudy dawn cut-off) is below the alert threshold
    assert not check.is_truncated(datetime(2026, 10, 28, 7, 45), 120.0)
    # big value but late afternoon is not flagged
    assert not check.is_truncated(datetime(2026, 10, 28, 16, 0), 900.0)
    assert not check.is_truncated(datetime(2026, 10, 28, 10, 0), None)


def test_check_window_is_whole_days_before_today() -> None:
    start, end = check.get_check_window(NOW)
    assert end == datetime(2026, 10, 31)
    assert start == datetime(2026, 10, 24)


def _stub_session(rows):
    result = MagicMock()
    result.all.return_value = rows
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)

    @asynccontextmanager
    async def ctx():
        yield session

    return ctx, session


@pytest.mark.asyncio
async def test_check_alerts_on_truncated_day(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        (date(2026, 10, 27), datetime(2026, 10, 27, 19, 30), 0.0),
        (date(2026, 10, 28), datetime(2026, 10, 28, 9, 45), 845.2),
    ]
    ctx, session = _stub_session(rows)
    monkeypatch.setattr(check, "get_read_session", ctx)
    sentry = MagicMock()
    monkeypatch.setattr(check.sentry_sdk, "new_scope", sentry)

    result = await check.run_apvi_truncation_check(now=NOW)

    assert [t.day for t in result] == [date(2026, 10, 28)]
    sentry.return_value.__enter__.return_value.capture_message.assert_called_once()
    params = session.execute.await_args.args[1]
    assert params["unit_code"] == "ROOFTOP_APVI_WA"
    assert params["window_end"] == datetime(2026, 10, 31)


@pytest.mark.asyncio
async def test_check_quiet_when_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx, session = _stub_session([(date(2026, 10, 27), datetime(2026, 10, 27, 19, 30), 0.0)])
    monkeypatch.setattr(check, "get_read_session", ctx)
    sentry = MagicMock()
    monkeypatch.setattr(check.sentry_sdk, "new_scope", sentry)

    assert await check.run_apvi_truncation_check(now=NOW) == []
    sentry.assert_not_called()
    # read only: the single statement is the select
    assert session.execute.await_count == 1
    session.commit.assert_not_called()
