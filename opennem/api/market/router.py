"""
Market data router for OpenNEM API.

This module handles market-specific metrics like price and demand.
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_versionizer import api_version

from opennem.api.keys import api_protected
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.timeseries import format_timeseries_response
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.grouping import PrimaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import get_clickhouse_dependency
from opennem.utils.dates import get_last_completed_interval_for_network

router = APIRouter()
logger = logging.getLogger(__name__)

_SUPPORTED_METRICS = [
    Metric.PRICE,
    Metric.DEMAND,
    Metric.DEMAND_ENERGY,
]


@api_version(4)
@api_protected()
@router.get(
    "/network/{network_code}",
    response_model=APIV4ResponseSchema,
    response_model_exclude_none=True,
)
async def get_network_data(
    network_code: str,
    metrics: Annotated[list[Metric], Query(description="The metrics to get data for", example="price")],
    interval: Annotated[Interval, Query(description="The time interval to aggregate data by", example="1h")] = Interval.INTERVAL,
    date_start: Annotated[datetime | None, Query(description="Start time for the query", example="2024-01-01T00:00:00")] = None,
    date_end: Annotated[datetime | None, Query(description="End time for the query", example="2024-01-02T00:00:00")] = None,
    primary_grouping: Annotated[
        PrimaryGrouping, Query(description="Primary grouping to apply", example="network_region")
    ] = PrimaryGrouping.NETWORK,
    client: Any = Depends(get_clickhouse_dependency),
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

    # Get default dates if not provided
    if date_end is None:
        date_end = get_last_completed_interval_for_network(network=network)

    if date_start is None:
        date_start = interval.default_start(date_end)

    # Build and execute query using the unified query builder
    query, params, column_names = get_timeseries_query(
        query_type=QueryType.MARKET,
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping=primary_grouping,
    )

    # Execute query
    try:
        logger.debug(query)
        results = client.execute(query, params)
        logger.debug(f"got {len(results)} results")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e

    # Convert results to list of dictionaries using column names
    result_dicts = [dict(zip(column_names, row, strict=True)) for row in results]
    logger.debug(f"first row: {result_dicts[0] if result_dicts else None}")

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
    return APIV4ResponseSchema(data=timeseries_list)
