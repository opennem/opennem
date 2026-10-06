"""
Market data router for OpenNEM API.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_cache.decorator import cache
from fastapi_versionizer import api_version

from opennem.api.data.utils import get_max_interval_days, validate_date_range
from opennem.api.forecast import (
    SOURCE_INTERVAL,
    get_forecast_run_times,
    get_forecast_timeseries_query,
    get_latest_forecast_interval,
    is_forecast_metric,
)
from opennem.api.intervals import cap_date_end_to_settled_interval
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.schema import std_error_responses
from opennem.api.security import optional_user
from opennem.api.timeseries import build_timeseries_response, format_timeseries_response
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.grouping import PrimaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import execute_async, get_clickhouse_dependency
from opennem.schema.network import NetworkSchema
from opennem.users.schema import OpenNEMUser
from opennem.utils.dates import get_last_completed_interval_for_network

router = APIRouter()
logger = logging.getLogger("opennem.api.market")

_SUPPORTED_METRICS = [
    Metric.PRICE,
    Metric.DEMAND,
    Metric.DEMAND_ENERGY,
    Metric.CURTAILMENT,
    Metric.CURTAILMENT_ENERGY,
    Metric.CURTAILMENT_SOLAR_UTILITY,
    Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY,
    Metric.CURTAILMENT_WIND,
    Metric.CURTAILMENT_WIND_ENERGY,
    Metric.DEMAND,
    Metric.DEMAND_ENERGY,
    Metric.DEMAND_GROSS,
    Metric.DEMAND_GROSS_ENERGY,
    Metric.GENERATION_RENEWABLE,
    Metric.GENERATION_RENEWABLE_ENERGY,
    Metric.GENERATION_RENEWABLE_WITH_STORAGE,
    Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY,
    Metric.RENEWABLE_PROPORTION,
    Metric.RENEWABLE_WITH_STORAGE_PROPORTION,
    Metric.FLOW_IMPORTS,
    Metric.FLOW_EXPORTS,
    Metric.FLOW_IMPORTS_ENERGY,
    Metric.FLOW_EXPORTS_ENERGY,
    Metric.SOLAR_ROOFTOP_FORECAST,
]


@api_version(4)
@router.get("/network/{network_code}", responses=std_error_responses())
@cache(expire=60 * 5)
async def get_network_data(
    network_code: Annotated[
        str,
        Path(description="Network identifier — see `/networks` for valid codes.", examples=["NEM"]),
    ],
    metrics: Annotated[
        list[Metric],
        Query(
            description="One or more market metrics to return (`price`, `demand`, `curtailment`, …).",
            examples=[["price", "demand"]],
            min_length=1,
        ),
    ],
    interval: Annotated[
        Interval,
        Query(description="Bucket size for time-series aggregation.", examples=["1h"]),
    ] = Interval.INTERVAL,
    date_start: Annotated[
        datetime | None,
        Query(description="Inclusive start of the query window (network-local time).", examples=["2024-01-01T00:00:00"]),
    ] = None,
    date_end: Annotated[
        datetime | None,
        Query(description="Inclusive end of the query window (network-local time).", examples=["2024-01-02T00:00:00"]),
    ] = None,
    network_region: Annotated[
        str | None,
        Query(description="Restrict to a single network region (price zone).", examples=["NSW1"]),
    ] = None,
    primary_grouping: Annotated[
        PrimaryGrouping,
        Query(description="Primary grouping dimension applied to results.", examples=["network_region"]),
    ] = PrimaryGrouping.NETWORK,
    client: Any = Depends(get_clickhouse_dependency),
    user: optional_user = None,
) -> dict:
    """Get market data for a network.

    Forecast metrics (`*_forecast`) are served from the forecast table with their own date
    defaults: a live request runs from now to the end of the latest forecast run rather than
    ending at the last settled interval (#675).
    """
    network = get_api_network_from_code(network_code)
    validate_metrics(metrics, _SUPPORTED_METRICS)

    if network_region:
        primary_grouping = PrimaryGrouping.NETWORK_REGION

    forecast_metrics = [m for m in metrics if is_forecast_metric(m)]
    actual_metrics = [m for m in metrics if not is_forecast_metric(m)]

    timeseries_list: list[dict[str, Any]] = []
    found_rows = False

    if actual_metrics:
        actual, rows = await _actual_timeseries(
            client, network, actual_metrics, interval, date_start, date_end, network_region, primary_grouping, user
        )
        timeseries_list.extend(actual)
        found_rows |= rows

    if forecast_metrics:
        forecast, rows = await _forecast_timeseries(
            client, network, forecast_metrics, interval, date_start, date_end, network_region, primary_grouping, user
        )
        timeseries_list.extend(forecast)
        found_rows |= rows

    if not found_rows:
        raise HTTPException(
            status_code=404,
            detail=f"No market data available for network {network_code} in the specified time range",
        )

    # mixed requests come back in the order the metrics were asked for; a single family is
    # already in request order (including repeated metrics) and is left alone
    if actual_metrics and forecast_metrics:
        order: dict[str, int] = {}
        for i, m in enumerate(metrics):
            order.setdefault(m.value, i)
        timeseries_list.sort(key=lambda ts: order.get(ts["metric"], len(order)))

    return build_timeseries_response(timeseries_list)


async def _run_query(client: Any, query: str, params: dict[str, Any]) -> list[Any]:
    start_time = time.time()
    try:
        logger.debug(query, params)
        results = await execute_async(client, query, params)
        logger.debug(f"Query execution time: {(time.time() - start_time) * 1000:.2f} ms")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e
    return results or []


async def _actual_timeseries(
    client: Any,
    network: NetworkSchema,
    metrics: list[Metric],
    interval: Interval,
    date_start: datetime | None,
    date_end: datetime | None,
    network_region: str | None,
    primary_grouping: PrimaryGrouping,
    user: OpenNEMUser | None,
) -> tuple[list[dict[str, Any]], bool]:
    live_query = date_end is None

    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    if date_start > date_end:
        raise HTTPException(status_code=400, detail="Date start must be before date end")

    # Live request: don't serve the provisional bleeding-edge interval (#575).
    if live_query:
        date_end = await cap_date_end_to_settled_interval(
            client=client, network=network, query_type=QueryType.MARKET, date_end=date_end
        )

    query, params, column_names = get_timeseries_query(
        query_type=QueryType.MARKET,
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping=primary_grouping,
        network_region=network_region,
    )

    results = await _run_query(client, query, params)
    if not results:
        return [], False

    result_dicts = [dict(zip(column_names, row, strict=True)) for row in results]

    timeseries_list = format_timeseries_response(
        network=network.code,
        metrics=metrics,
        interval=interval,
        primary_grouping=primary_grouping,
        secondary_groupings=None,
        results=result_dicts,
    )
    return timeseries_list, True


async def _forecast_timeseries(
    client: Any,
    network: NetworkSchema,
    metrics: list[Metric],
    interval: Interval,
    date_start: datetime | None,
    date_end: datetime | None,
    network_region: str | None,
    primary_grouping: PrimaryGrouping,
    user: OpenNEMUser | None,
) -> tuple[list[dict[str, Any]], bool]:
    # forecasts look forward: the window starts now unless the caller says otherwise
    start_defaulted = date_start is None
    if date_start is None:
        date_start = get_last_completed_interval_for_network(network=network, tz_aware=False)

    if date_end is None:
        latest = await get_latest_forecast_interval(client, network, metrics)
        if latest is None:
            return [], False

        # exclusive end that still takes in the last row's 5 minute steps
        date_end = latest + SOURCE_INTERVAL

        # a stale forecast that ends before the window starts is no rows, not a bad request
        if date_end <= date_start:
            return [], False

        if start_defaulted:
            # keep the default window inside the plan's range for this interval
            date_end = min(date_end, date_start + timedelta(days=get_max_interval_days(interval, user)))

    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    if date_start > date_end:
        raise HTTPException(status_code=400, detail="Date start must be before date end")

    query, params, column_names = get_forecast_timeseries_query(
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping=primary_grouping,
        network_region=network_region,
    )

    results = await _run_query(client, query, params)
    if not results:
        return [], False

    result_dicts = [dict(zip(column_names, row, strict=True)) for row in results]

    timeseries_list = format_timeseries_response(
        network=network.code,
        metrics=metrics,
        interval=interval,
        primary_grouping=primary_grouping,
        secondary_groupings=None,
        results=result_dicts,
    )

    run_times = await get_forecast_run_times(client, network, metrics, date_start, date_end, network_region)
    network_tz = network.get_fixed_offset()
    for ts in timeseries_list:
        run_time = run_times.get(Metric(ts["metric"]))
        ts["forecast_run_time"] = run_time.astimezone(network_tz).isoformat() if run_time else None

    return timeseries_list, True
