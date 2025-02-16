"""
API router for OpenNEM data endpoints.

This module contains the FastAPI router for data endpoints, including time series
data queries.
"""

import logging
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_versionizer import api_version

from opennem.api.data.utils import get_default_start_date, validate_date_range
from opennem.api.keys import api_protected
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.timeseries import format_timeseries_response
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import get_clickhouse_dependency
from opennem.utils.dates import get_last_completed_interval_for_network

router = APIRouter()
logger = logging.getLogger("opennem.api.data")

_SUPPORTED_METRICS = [
    Metric.ENERGY,
    Metric.POWER,
    Metric.EMISSIONS,
    Metric.MARKET_VALUE,
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
    metrics: Annotated[list[Metric], Query(description="The metrics to get data for", example="energy")],
    interval: Annotated[Interval, Query(description="The time interval to aggregate data by", example="1h")] = Interval.INTERVAL,
    date_start: Annotated[datetime | None, Query(description="Start time for the query", example="2024-01-01T00:00:00")] = None,
    date_end: Annotated[datetime | None, Query(description="End time for the query", example="2024-01-02T00:00:00")] = None,
    primary_grouping: Annotated[
        PrimaryGrouping, Query(description="Primary grouping to apply", example="network_region")
    ] = PrimaryGrouping.NETWORK,
    secondary_grouping: Annotated[
        SecondaryGrouping | None, Query(description="Optional secondary grouping to apply", example="fueltech_group")
    ] = None,
    client: Any = Depends(get_clickhouse_dependency),
) -> APIV4ResponseSchema:
    """
    Get time series data for a network.

    This endpoint returns time series data for a network, with optional grouping
    by region and other dimensions. The data can be aggregated by different time
    intervals.

    Args:
        network_code: The network to get data for
        metrics: List of metrics to query (e.g. energy, power, price)
        interval: The time interval to aggregate by
        date_start: Start time for the query
        date_end: End time for the query
        primary_grouping: Primary grouping to apply
        secondary_grouping: Optional secondary grouping to apply
        client: ClickHouse client dependency

    Returns:
        APIV4ResponseSchema: Time series data response containing a list of TimeSeries objects,
        one per requested metric
    """
    # Get the network schema
    network = get_api_network_from_code(network_code)

    # validate metrics
    validate_metrics(metrics, _SUPPORTED_METRICS)

    # Get default dates if not provided
    if date_end is None:
        date_end = get_last_completed_interval_for_network(network=network)

    if date_start is None:
        date_start = get_default_start_date(interval, date_end)

    # Validate the date range for the interval
    validate_date_range(interval, date_start, date_end)

    # Convert single secondary grouping to sequence
    secondary_groupings = [secondary_grouping] if secondary_grouping else None

    # Build and execute query using the unified query builder
    query, params, column_names = get_timeseries_query(
        query_type=QueryType.DATA,
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping=primary_grouping,
        secondary_groupings=secondary_groupings,
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
        secondary_groupings=secondary_groupings,
        results=result_dicts,
    )

    # Return all TimeSeries objects, one per metric
    return APIV4ResponseSchema(data=timeseries_list)
