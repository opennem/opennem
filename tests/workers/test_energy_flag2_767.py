"""#767: flag-2 rows holding generated/12 after a scada re-delivery. No database."""

import importlib.util
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from opennem.controllers import nem
from opennem.controllers.schema import ControllerReturn
from opennem.db.bulk_insert_csv import build_insert_query
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.monitors import energy_quality_flag as guard
from opennem.workers import energy

NOW = datetime(2026, 10, 24, 12, 0)


def _sql(query) -> str:
    return " ".join(str(query).split())


# upsert SQL


def _conflict_clause(update_cols: list[str], keep: bool) -> str:
    _, queries = build_insert_query(FacilityScada, update_cols, keep_processed_energy=keep)
    return " ".join(queries[2].split())


def test_default_upsert_unchanged() -> None:
    sql = _conflict_clause(["generated", "energy"], keep=False)
    assert "generated = EXCLUDED.generated, energy = EXCLUDED.energy" in sql
    assert "CASE" not in sql


def test_keep_processed_energy_guards_energy_and_flag_only() -> None:
    sql = _conflict_clause(nem.SCADA_UPDATE_COLUMNS, keep=True)
    assert "generated = EXCLUDED.generated" in sql
    guard_expr = "facility_scada.generated IS NOT DISTINCT FROM EXCLUDED.generated"
    assert f"energy = CASE WHEN {guard_expr} THEN facility_scada.energy ELSE EXCLUDED.energy END" in sql
    assert (
        f"energy_quality_flag = CASE WHEN {guard_expr} THEN facility_scada.energy_quality_flag "
        "ELSE EXCLUDED.energy_quality_flag END"
    ) in sql
    assert sql.count("CASE") == 2


def test_unit_solution_keeps_energy_storage_unconditional() -> None:
    sql = _conflict_clause(nem.UNIT_SOLUTION_UPDATE_COLUMNS, keep=True)
    assert "energy_storage = EXCLUDED.energy_storage" in sql
    assert sql.count("CASE") == 2


def test_guard_is_noop_for_tables_without_energy_columns() -> None:
    _, queries = build_insert_query(BalancingSummary, ["demand"], keep_processed_energy=True)
    assert "CASE" not in queries[2]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fn", "table_name"),
    [
        ("process_unit_scada_optimized", "unit_scada"),
        ("process_unit_solution", "unit_solution"),
        ("process_meter_data_gen_duid", "meter"),
        ("process_rooftop_actual", "rooftop"),
        ("process_rooftop_forecast", "rooftop_forecast"),
    ],
)
async def test_every_nem_scada_call_site_uses_guarded_upsert(monkeypatch: pytest.MonkeyPatch, fn: str, table_name: str) -> None:
    record = {
        "network_id": "NEM",
        "interval": datetime(2026, 10, 5, 13, 45),
        "facility_code": "X",
        "generated": 1.0,
        "eoi_quantity": None,
        "is_forecast": False,
        "energy_quality_flag": 0,
        "energy": 1 / 12,
        "energy_storage": None,
    }
    monkeypatch.setattr(nem, "generate_facility_scada", AsyncMock(return_value=[record]))
    monkeypatch.setattr(nem, "rooftop_remap_regionids", lambda r: r)
    monkeypatch.setattr(nem, "insert_new_forecast_runs", AsyncMock())
    monkeypatch.setattr(nem, "rooftop_forecast_rows", lambda r: [])
    monkeypatch.setattr(nem, "_has_rooftop_measurement", lambda r: True)
    bulk = AsyncMock(return_value=1)
    monkeypatch.setattr(nem, "bulkinsert_mms_items", bulk)

    table = MagicMock()
    table.records = [{"power": 1}]
    cr = await getattr(nem, fn)(table)

    bulk.assert_awaited_once()
    args, kwargs = bulk.await_args
    assert args[0] is FacilityScada
    assert kwargs == {"keep_processed_energy": True}
    assert "energy_quality_flag" in args[2] and "energy" in args[2]
    if fn in ("process_unit_solution", "process_meter_data_gen_duid"):
        assert cr.interval_min == cr.interval_max == record["interval"]


def test_wem_paths_untouched() -> None:
    source = (Path(__file__).parents[2] / "opennem" / "controllers" / "wem.py").read_text()
    assert "keep_processed_energy" not in source
    assert 'FacilityScada, records_to_store, ["generated", "energy"]' in source


# worker SQL


def test_worker_update_selects_unprocessed_or_non_trapezoid_nem_rows() -> None:
    sql = _sql(energy.ENERGY_UPDATE_QUERY)
    assert "fs.energy_quality_flag < 2" in sql
    assert "fs.network_id = 'NEM'" in sql
    assert "abs(fs.energy - (rs.generated + rs.prev_generated) / 2 / nd.intervals_per_hour) > :energy_tolerance" in sql
    assert "rs.prev_generated IS NOT NULL" in sql


def test_worker_update_keeps_network_exclusions_and_window() -> None:
    sql = _sql(energy.ENERGY_UPDATE_QUERY)
    assert "network_id not in ('WEM', 'WEMDE', 'AEMO_ROOFTOP_BACKFILL')" in sql
    # the extra condition never widens the scan: rows are still bounded by the interval range
    assert "fs.interval BETWEEN :start_time AND :end_time" in sql
    assert "interval BETWEEN :lag_start AND :end_time" in sql


def test_worker_params_use_small_tolerance_and_lag_start() -> None:
    params = energy._energy_params(datetime(2026, 10, 5), datetime(2026, 10, 6))
    assert params["energy_tolerance"] == 0.0005 == energy.ENERGY_REPAIR_TOLERANCE
    assert params["lag_start"] == datetime(2026, 10, 5) - timedelta(minutes=5)


def test_tolerance_separates_fallback_from_trapezoid() -> None:
    # fallback - trapezoid = (generated - prev) / 24: a 1 MW change between intervals is 0.0417 MWh, far above tolerance,
    # while numeric(20,6) rounding noise (~1e-6) is far below it
    assert abs(1.0) / 24 > energy.ENERGY_REPAIR_TOLERANCE
    assert 1e-6 < energy.ENERGY_REPAIR_TOLERANCE


def test_mismatch_count_is_read_only_flag_2_nem() -> None:
    sql = _sql(energy.ENERGY_MISMATCH_COUNT_QUERY)
    assert sql.split("SELECT count(*)")[0].strip().startswith("WITH")
    assert "UPDATE" not in sql
    assert "fs.network_id = 'NEM'" in sql and "fs.energy_quality_flag = 2" in sql


@pytest.mark.asyncio
async def test_calculate_energy_runs_update_with_params() -> None:
    result = MagicMock(rowcount=7)
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    session.commit = AsyncMock()

    rows = await energy._calculate_energy_for_interval(session, datetime(2026, 10, 5), datetime(2026, 10, 6))

    assert rows == 7
    query, params = session.execute.await_args.args
    assert query is energy.ENERGY_UPDATE_QUERY
    assert params["energy_tolerance"] == 0.0005
    session.commit.assert_awaited_once()


# per day task


@pytest.mark.asyncio
async def test_per_day_task_reprocess_window_covers_meter_file_span(monkeypatch: pytest.MonkeyPatch) -> None:
    from opennem.tasks import tasks

    async def fake_run_crawl(crawler, **kwargs):
        if crawler.name == tasks.AEMONEMNextDayDispatch.name:
            return ControllerReturn(
                inserted_records=5, interval_min=datetime(2026, 10, 21, 4, 5), interval_max=datetime(2026, 10, 23, 4, 0)
            )
        return ControllerReturn(inserted_records=5, interval_min=datetime(2026, 10, 20, 4, 5))

    reprocess = AsyncMock()
    monkeypatch.setattr(tasks, "run_crawl", fake_run_crawl)
    monkeypatch.setattr(tasks, "reprocess_energy_window", reprocess)
    monkeypatch.setattr(tasks, "get_last_completed_interval_for_network", lambda **_: NOW)

    await tasks.task_nem_per_day_check({"job_try": 1})

    reprocess.assert_awaited_once_with(date_start=datetime(2026, 10, 20, 4, 5), date_end=NOW)


# guard


def test_mismatch_sample_day_is_4_to_10_days_back_and_rotates() -> None:
    seen = set()
    for i in range(14):
        now = NOW + timedelta(days=i)
        start, end = guard.get_mismatch_sample_day(now)
        back = (now.replace(hour=0, minute=0) - start).days
        assert 4 <= back <= 10
        assert start.hour == 0 and end == start + timedelta(hours=23, minutes=55)
        seen.add(back)
    assert seen == set(range(4, 11))


def _stub_count(monkeypatch: pytest.MonkeyPatch, total: int) -> AsyncMock:
    @asynccontextmanager
    async def ctx():
        yield MagicMock()

    count = AsyncMock(return_value=total)
    monkeypatch.setattr(guard, "get_read_session", ctx)
    monkeypatch.setattr(guard, "count_energy_mismatches", count)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_enabled", True)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_mismatch_threshold", 200)
    return count


@pytest.mark.asyncio
async def test_mismatch_guard_alerts_above_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    count = _stub_count(monkeypatch, 4908)
    sentry = MagicMock()
    monkeypatch.setattr(guard.sentry_sdk, "new_scope", sentry)

    result = await guard.run_energy_mismatch_check(now=NOW)

    assert result is not None and result.total == 4908
    sentry.return_value.__enter__.return_value.capture_message.assert_called_once()
    start, end = count.await_args.args[1:]
    assert end - start == timedelta(hours=23, minutes=55)


@pytest.mark.asyncio
async def test_mismatch_guard_quiet_at_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_count(monkeypatch, 200)
    sentry = MagicMock()
    monkeypatch.setattr(guard.sentry_sdk, "new_scope", sentry)

    assert (await guard.run_energy_mismatch_check(now=NOW)) is not None
    sentry.assert_not_called()


@pytest.mark.asyncio
async def test_mismatch_guard_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    count = _stub_count(monkeypatch, 5)
    monkeypatch.setattr(guard.settings, "energy_flag_guard_enabled", False)

    assert await guard.run_energy_mismatch_check(now=NOW) is None
    count.assert_not_awaited()


# repair script

_SPEC = importlib.util.spec_from_file_location("energy_backfill_767", Path(__file__).parents[2] / "bin" / "energy_backfill.py")
assert _SPEC and _SPEC.loader
backfill = importlib.util.module_from_spec(_SPEC)
sys.modules["energy_backfill_767"] = backfill
_SPEC.loader.exec_module(backfill)


def test_repair_flag_parses_and_defaults_to_dry_run() -> None:
    args = backfill.parse_args(["--repair", "--start", "2026-03-14", "--end", "2026-10-23"])
    assert args.repair and not args.apply and args.chunk_days == 3 and args.max_workers == 2


def test_repair_keeps_prod_write_guard() -> None:
    args = backfill.parse_args(["--repair", "--start", "2026-03-14", "--end", "2026-10-23", "--apply"])
    assert backfill.check_write_allowed(args, "db-prod.example.com")
    assert backfill.check_write_allowed(args, "db-dev") is None


@pytest.mark.asyncio
async def test_repair_dry_run_counts_without_writing(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from opennem import settings

    @asynccontextmanager
    async def ctx():
        yield MagicMock()

    count = AsyncMock(return_value=42)
    backlog = AsyncMock()
    monkeypatch.setattr(settings, "db_url", "postgresql+asyncpg://u:pw@db-dev:5432/opennem")
    monkeypatch.setattr("opennem.db.get_read_session", ctx)
    monkeypatch.setattr("opennem.workers.energy.count_energy_mismatches", count)
    monkeypatch.setattr("opennem.workers.energy.run_energy_backlog", backlog)

    code = await backfill.main(["--repair", "--start", "2026-10-01", "--end", "2026-10-07"])

    out = capsys.readouterr().out
    assert code == 0 and "flag 2 rows off the trapezoid" in out and "dry run" in out and "pw" not in out
    assert count.await_count == 2
    backlog.assert_not_awaited()


@pytest.mark.asyncio
async def test_repair_prod_apply_refused_without_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from opennem import settings

    backlog = AsyncMock()
    monkeypatch.setattr(settings, "db_url", "postgresql+asyncpg://u:pw@db-prod:5432/opennem")
    monkeypatch.setattr("opennem.workers.energy.run_energy_backlog", backlog)

    code = await backfill.main(["--repair", "--start", "2026-10-01", "--end", "2026-10-07", "--apply"])

    assert code == 3
    backlog.assert_not_awaited()
