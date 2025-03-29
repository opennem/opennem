"""
Market data router for OpenNEM API.

This module handles market-specific metrics like price and demand.
"""

import logging
import time
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import ORJSONResponse
from fastapi_cache.decorator import cache
from fastapi_versionizer import api_version

from opennem.api.data.utils import validate_date_range
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.security import authenticated_user
from opennem.api.timeseries import format_timeseries_response
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.grouping import PrimaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import get_clickhouse_dependency

router = APIRouter()
logger = logging.getLogger(__name__)

_SUPPORTED_METRICS = [
    Metric.PRICE,
    Metric.DEMAND,
    Metric.DEMAND_ENERGY,
]


@api_version(4)
@router.get(
    "/network/{network_code}",
    response_model=APIV4ResponseSchema,
    response_model_exclude_none=True,
)
@cache(expire=60 * 5)
async def get_network_data(
    network_code: str,
    metrics: Annotated[list[Metric], Query(description="The metrics to get data for", example="price")],
    interval: Annotated[Interval, Query(description="The time interval to aggregate data by", example="1h")] = Interval.INTERVAL,
    date_start: Annotated[datetime | None, Query(description="Start time for the query", example="2024-01-01T00:00:00")] = None,
    date_end: Annotated[datetime | None, Query(description="End time for the query", example="2024-01-02T00:00:00")] = None,
    network_region: Annotated[str | None, Query(description="Network region to get data for", example="NSW1")] = None,
    primary_grouping: Annotated[
        PrimaryGrouping, Query(description="Primary grouping to apply", example="network_region")
    ] = PrimaryGrouping.NETWORK,
    client: Any = Depends(get_clickhouse_dependency),
    user: authenticated_user = None,
) -> APIV4ResponseSchema:
    """
    Get market data for a network.

    This endpoint returns market data like price and demand, with optional grouping
    by region. The data can be aggregated by different time intervals.

    Args:
        network_code: The network to get data for
        metrics: List of metrics to query (e.g. price, demand)
        interval: The time interval to aggregate by
        date_start: Start time for the query
        date_end: End time for the query
        primary_grouping: Primary grouping to apply
        client: ClickHouse client dependency

    Returns:
        APIV4ResponseSchema: Time series data response containing a list of TimeSeries objects,
        one per requested metric
    """
    # Get the network schema
    network = get_api_network_from_code(network_code)

    # Validate metrics
    validate_metrics(metrics, _SUPPORTED_METRICS)

    if network_region:
        primary_grouping = PrimaryGrouping.NETWORK_REGION

    # validate date range
    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    if date_start > date_end:
        raise HTTPException(status_code=400, detail="Date start must be before date end")

    # Build and execute query using the unified query builder
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

    # Execute query
    start_time = time.time()
    try:
        logger.debug(query, params)
        results = client.execute(query, params)
        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(f"Query execution time: {elapsed_ms:.2f} ms")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e

    # Check if we got any results
    if not results:
        logger.info(f"No market data found for network {network_code} in time range {date_start} to {date_end}")
        raise HTTPException(
            status_code=416,
            detail=f"No market data available for network {network_code} in the specified time range",
        )

    # Convert results to list of dictionaries using column names
    result_dicts = [dict(zip(column_names, row, strict=True)) for row in results]

    # Transform results into response format - returns one TimeSeries per metric
    timeseries_list = format_timeseries_response(
        network=network.code,
        metrics=metrics,
        interval=interval,
        primary_grouping=primary_grouping,
        secondary_groupings=None,
        results=result_dicts,
    )

    # Return all TimeSeries objects, one per metric
    return ORJSONResponse(APIV4ResponseSchema(data=timeseries_list).model_dump())
