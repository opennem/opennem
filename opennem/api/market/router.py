"""
Market data router for OpenNEM API.
"""

import logging
import time
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi_cache.decorator import cache
from fastapi_versionizer import api_version

from opennem.api.data.utils import validate_date_range
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.schema import std_error_responses
from opennem.api.security import authenticated_user
from opennem.api.timeseries import build_timeseries_response, format_timeseries_response
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.grouping import PrimaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import execute_async, get_clickhouse_dependency

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
    user: authenticated_user | None = None,
) -> dict:
    """Get market data for a network."""
    network = get_api_network_from_code(network_code)
    validate_metrics(metrics, _SUPPORTED_METRICS)

    if network_region:
        primary_grouping = PrimaryGrouping.NETWORK_REGION

    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    if date_start > date_end:
        raise HTTPException(status_code=400, detail="Date start must be before date end")

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

    start_time = time.time()
    try:
        logger.debug(query, params)
        results = await execute_async(client, query, params)
        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(f"Query execution time: {elapsed_ms:.2f} ms")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No market data available for network {network_code} in the specified time range",
        )

    result_dicts = [dict(zip(column_names, row, strict=True)) for row in results]

    timeseries_list = format_timeseries_response(
        network=network.code,
        metrics=metrics,
        interval=interval,
        primary_grouping=primary_grouping,
        secondary_groupings=None,
        results=result_dicts,
    )

    return build_timeseries_response(timeseries_list)
