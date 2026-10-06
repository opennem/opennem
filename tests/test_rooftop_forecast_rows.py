"""AEMO ROOFTOP_PV FORECAST records into market_forecast_intervals rows (#675)."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from opennem.aggregates import forecast
from opennem.aggregates.forecast import ROOFTOP_FORECAST_METRIC, ROOFTOP_FORECAST_SOURCE, rooftop_forecast_rows
from opennem.controllers import nem


def _record(region: str, interval: str, powermean: str | None, run: str = "2026/10/06 11:00:00") -> dict:
    # shape and string values as parse_aemo_mms_csv hands them to process_rooftop_forecast
    return {
        "version_datetime": run,
        "regionid": region,
        "interval_datetime": interval,
        "powermean": powermean,
        "powerpoe50": "1.0",
        "powerpoelow": "0.5",
        "powerpoehigh": "1.5",
        "lastchanged": "2026/10/06 10:51:57",
    }


def test_row_carries_run_time_horizon_and_version() -> None:
    (row,) = rooftop_forecast_rows([_record("NSW1", "2026/10/06 11:30:00", "5894.371")])

    interval, network_id, region, metric, source, value, run_time, horizon, version = row
    assert interval == datetime(2026, 10, 6, 11, 30)
    assert interval.tzinfo is None
    assert (network_id, region, metric, source) == ("NEM", "NSW1", ROOFTOP_FORECAST_METRIC, ROOFTOP_FORECAST_SOURCE)
    assert value == 5894.371
    # VERSION_DATETIME is AEST, the column is a real UTC instant
    assert run_time == datetime(2026, 10, 6, 1, 0, tzinfo=UTC)
    assert horizon == 30
    assert version == int(run_time.timestamp() * 1000)


def test_sub_regions_are_dropped() -> None:
    records = [_record(r, "2026/10/06 11:30:00", "10") for r in ("QLD1", "QLDC", "QLDN", "QLDS", "TASN", "TASS", "TAS1")]

    assert [row[2] for row in rooftop_forecast_rows(records)] == ["QLD1", "TAS1"]


def test_blank_powermean_is_no_row_not_zero() -> None:
    records = [_record("SA1", "2026/10/06 11:30:00", ""), _record("SA1", "2026/10/06 12:00:00", None)]

    assert rooftop_forecast_rows(records) == []


def test_newer_run_has_higher_version() -> None:
    older = rooftop_forecast_rows([_record("VIC1", "2026/10/06 12:00:00", "1", run="2026/10/06 10:30:00")])[0]
    newer = rooftop_forecast_rows([_record("VIC1", "2026/10/06 12:00:00", "2", run="2026/10/06 11:00:00")])[0]

    assert newer[-1] > older[-1]
    assert (older[-2], newer[-2]) == (90, 60)


def test_stored_run_is_not_inserted_again() -> None:
    rows = rooftop_forecast_rows(
        [
            _record("NSW1", "2026/10/06 11:30:00", "1", run="2026/10/06 11:00:00"),
            _record("NSW1", "2026/10/06 11:00:00", "2", run="2026/10/06 10:30:00"),
        ]
    )
    stored = {rows[0][-1]}  # the 11:00 run is already in ch, the 10:30 run is not

    async def _exists(metric: str, version: int, interval_from: datetime) -> bool:
        return version in stored

    insert = AsyncMock(side_effect=lambda r: len(r))
    with patch.object(forecast, "_run_already_stored", _exists), patch.object(forecast, "insert_forecast_rows", insert):
        inserted = asyncio.run(forecast.insert_new_forecast_runs(rows))

    assert inserted == 1
    assert [r[-1] for r in insert.await_args.args[0]] == [rows[1][-1]]


def test_clickhouse_failure_keeps_the_pg_write() -> None:
    """the static exports read the pg rows, so a ch error must not fail the crawl"""
    table = SimpleNamespace(records=[_record("NSW1", "2026/10/06 11:30:00", "5894.371")])
    pg_rows = [{"facility_code": "NSW1", "interval": datetime(2026, 10, 6, 11, 30), "generated": 5894.371}]

    with (
        patch.object(nem, "generate_facility_scada", AsyncMock(return_value=pg_rows)),
        patch.object(nem, "rooftop_remap_regionids", side_effect=lambda r: r),
        patch.object(nem, "bulkinsert_mms_items", AsyncMock(return_value=1)) as bulk,
        patch.object(nem, "insert_new_forecast_runs", AsyncMock(side_effect=RuntimeError("ch down"))),
    ):
        cr = asyncio.run(nem.process_rooftop_forecast(table))  # type: ignore[arg-type]

    bulk.assert_awaited_once()
    assert cr.inserted_records == 1
