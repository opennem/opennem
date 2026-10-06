"""AEMO ROOFTOP_PV FORECAST records into market_forecast_intervals rows (#675)."""

from datetime import UTC, datetime

from opennem.aggregates.forecast import ROOFTOP_FORECAST_METRIC, ROOFTOP_FORECAST_SOURCE, rooftop_forecast_rows


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
