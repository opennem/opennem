"""Forecast metric query builder and market router defaults (#675)."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opennem.api.forecast import FORECAST_METRICS, get_forecast_timeseries_query, is_forecast_metric
from opennem.api.market import router as market_router
from opennem.api.timeseries import _expected_buckets
from opennem.core.grouping import PrimaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval, get_interval_function
from opennem.schema.network import NetworkNEM

START = datetime(2026, 10, 6, 10, 0)
END = datetime(2026, 10, 7, 10, 0)


def test_forecast_metric_registry() -> None:
    assert FORECAST_METRICS == {Metric.SOLAR_ROOFTOP_FORECAST: "solar_rooftop"}
    assert is_forecast_metric(Metric.SOLAR_ROOFTOP_FORECAST)
    assert not is_forecast_metric(Metric.PRICE)


def test_network_total_needs_every_region() -> None:
    sql, params, columns = get_forecast_timeseries_query(
        NetworkNEM, [Metric.SOLAR_ROOFTOP_FORECAST], Interval.INTERVAL, START, END
    )

    assert columns == ["interval", "network", "solar_rooftop_forecast"]
    assert params["regions_required"] == 5
    assert params["metrics"] == ("solar_rooftop",)
    assert "solar_rooftop_regions >= %(regions_required)s" in sql
    assert "market_forecast_intervals FINAL" in sql


def test_region_grouping_and_filter_need_one_region() -> None:
    _, by_region, columns = get_forecast_timeseries_query(
        NetworkNEM,
        [Metric.SOLAR_ROOFTOP_FORECAST],
        Interval.INTERVAL,
        START,
        END,
        primary_grouping=PrimaryGrouping.NETWORK_REGION,
    )
    _, filtered, _ = get_forecast_timeseries_query(
        NetworkNEM, [Metric.SOLAR_ROOFTOP_FORECAST], Interval.INTERVAL, START, END, network_region="SA1"
    )

    assert columns == ["interval", "network", "network_region", "solar_rooftop_forecast"]
    assert by_region["regions_required"] == 1
    assert filtered["regions_required"] == 1
    assert filtered["network_region"] == "SA1"


def test_steps_cover_the_window_start() -> None:
    """A row labelled T fills T..T+25m, so the row covering an off-grid start begins up to 25m earlier"""
    sql, params, _ = get_forecast_timeseries_query(
        NetworkNEM, [Metric.SOLAR_ROOFTOP_FORECAST], Interval.INTERVAL, datetime(2026, 10, 6, 10, 15), END
    )

    assert params["source_start"] == datetime(2026, 10, 6, 9, 50)
    assert "ARRAY JOIN [0, 5, 10, 15, 20, 25] AS step" in sql
    assert "raw_interval >= %(date_start)s AND raw_interval < %(date_end)s" in sql


def test_thirty_minute_bucket() -> None:
    sql, _, _ = get_forecast_timeseries_query(NetworkNEM, [Metric.SOLAR_ROOFTOP_FORECAST], Interval.HALF_HOUR, START, END)

    assert "toStartOfInterval(raw_interval, INTERVAL 30 minute) AS interval" in sql


def test_actual_metric_is_refused() -> None:
    with pytest.raises(ValueError):
        get_forecast_timeseries_query(NetworkNEM, [Metric.PRICE], Interval.INTERVAL, START, END)


def test_half_hour_interval_everywhere() -> None:
    assert Interval("30m") is Interval.HALF_HOUR
    assert get_interval_function(Interval.HALF_HOUR, "x") == "time_bucket('30 minutes', x)"
    assert _expected_buckets(Interval.HALF_HOUR, START, START + timedelta(hours=1)) == [
        START,
        START + timedelta(minutes=30),
        START + timedelta(hours=1),
    ]


def _run_forecast(date_start: datetime | None, date_end: datetime | None, latest: datetime | None) -> MagicMock:
    builder = MagicMock()

    def _capture(**kwargs):  # noqa: ANN202
        builder(**kwargs)
        return "SQL", {}, ["interval", "network", "solar_rooftop_forecast"]

    with (
        patch.object(market_router, "get_latest_forecast_interval", AsyncMock(return_value=latest)),
        patch.object(market_router, "get_last_completed_interval_for_network", return_value=START),
        patch.object(market_router, "get_forecast_timeseries_query", side_effect=_capture),
        patch.object(market_router, "_run_query", AsyncMock(return_value=[(START, "NEM", 1000.0)])),
        patch.object(
            market_router,
            "get_forecast_run_times",
            AsyncMock(return_value={Metric.SOLAR_ROOFTOP_FORECAST: datetime(2026, 10, 6, 0, 30, tzinfo=UTC)}),
        ),
    ):
        series, found = asyncio.run(
            market_router._forecast_timeseries(
                None,
                NetworkNEM,
                [Metric.SOLAR_ROOFTOP_FORECAST],
                Interval.INTERVAL,
                date_start,
                date_end,
                None,
                PrimaryGrouping.NETWORK,
                None,
            )
        )
    builder.series = series
    builder.found = found
    return builder


def test_live_request_runs_from_now_to_the_latest_run() -> None:
    builder = _run_forecast(None, None, latest=START + timedelta(days=2))

    kwargs = builder.call_args.kwargs
    assert kwargs["date_start"] == START
    # exclusive end takes in the last row's six 5 minute steps
    assert kwargs["date_end"] == START + timedelta(days=2, minutes=30)
    assert builder.found
    assert builder.series[0]["forecast_run_time"] == "2026-10-06T10:30:00+10:00"


def test_live_window_is_clamped_to_the_plan_range() -> None:
    builder = _run_forecast(None, None, latest=START + timedelta(days=30))

    # anonymous (community) 5m limit is 8 days
    assert builder.call_args.kwargs["date_end"] == START + timedelta(days=8)


def test_future_date_end_is_not_capped() -> None:
    future_end = START + timedelta(days=3)
    builder = _run_forecast(START, future_end, latest=START + timedelta(days=7))

    assert builder.call_args.kwargs["date_end"] == future_end


def test_no_forecast_rows_is_empty_not_error() -> None:
    builder = _run_forecast(None, None, latest=None)

    assert builder.call_count == 0
    assert builder.found is False


def test_start_defaults_to_now_when_only_end_is_given() -> None:
    builder = _run_forecast(None, START + timedelta(days=1), latest=START + timedelta(days=7))

    assert builder.call_args.kwargs["date_start"] == START


def test_stale_forecast_is_empty_not_a_bad_request() -> None:
    builder = _run_forecast(None, None, latest=START - timedelta(hours=1))

    assert builder.call_count == 0
    assert builder.found is False
