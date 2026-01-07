"""
API router for OpenNEM data endpoints.

This module contains the FastAPI router for data endpoints, including time series
data queries.
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
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import get_clickhouse_dependency

router = APIRouter()
logger = logging.getLogger("opennem.api.data")

_SUPPORTED_METRICS = [
    Metric.ENERGY,
    Metric.POWER,
    Metric.EMISSIONS,
    Metric.MARKET_VALUE,
    Metric.STORAGE_BATTERY,
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
    metrics: Annotated[list[Metric], Query(description="The metrics to get data for", example="energy")],
    interval: Annotated[Interval, Query(description="The time interval to aggregate data by", example="1h")] = Interval.INTERVAL,
    date_start: Annotated[datetime | None, Query(description="Start time for the query", example="2024-01-01T00:00:00")] = None,
    date_end: Annotated[datetime | None, Query(description="End time for the query", example="2024-01-02T00:00:00")] = None,
    network_region: Annotated[str | None, Query(description="Network region to get data for", example="NSW1")] = None,
    fueltech: Annotated[list[str] | None, Query(description="Fueltechs to get data for", example="coal_black")] = None,
    fueltech_group: Annotated[list[str] | None, Query(description="Fueltech groups to get data for", example="coal")] = None,
    primary_grouping: Annotated[
        PrimaryGrouping, Query(description="Primary grouping to apply", example="network_region")
    ] = PrimaryGrouping.NETWORK,
    secondary_grouping: Annotated[
        SecondaryGrouping | None, Query(description="Optional secondary grouping to apply", example="fueltech_group")
    ] = None,
    client: Any = Depends(get_clickhouse_dependency),
    user: authenticated_user = None,
) -> ORJSONResponse:
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

    # Validate the date range for the interval
    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    if date_start > date_end:
        raise HTTPException(status_code=400, detail="Date start must be before date end")

    # Convert single secondary grouping to sequence
    secondary_groupings = [secondary_grouping] if secondary_grouping else None

    if network_region:
        primary_grouping = PrimaryGrouping.NETWORK_REGION

    if fueltech:
        secondary_groupings = [SecondaryGrouping.FUELTECH]

    if fueltech_group:
        secondary_groupings = [SecondaryGrouping.FUELTECH_GROUP]

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
        # filters
        network_region=network_region,
        fueltech=fueltech,
        fueltech_group=fueltech_group,
    )

    # Execute query and log the timing of the query
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
        logger.info(f"No data found for network {network_code} in time range {date_start} to {date_end}")
        raise HTTPException(
            status_code=416,
            detail=f"No data available for network {network_code} in the specified time range",
        )

    # Convert results to list of dictionaries using column names
    result_dicts = [dict(zip(column_names, row, strict=True)) for row in results]

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
    return ORJSONResponse(APIV4ResponseSchema(data=timeseries_list).model_dump())


@api_version(4)
@router.get(
    "/facilities/{network_code}",
    response_model=APIV4ResponseSchema,
    response_model_exclude_none=True,
)
@cache(expire=60 * 5)
async def get_facility_data(
    network_code: str,
    metrics: Annotated[list[Metric], Query(description="The metrics to get data for", example="energy")],
    interval: Annotated[Interval, Query(description="The time interval to aggregate data by", example="1h")] = Interval.INTERVAL,
    facility_code: Annotated[
        list[str] | None, Query(description="The facility code to get data for", example="AEMO_DISCOS_01")
    ] = None,
    date_start: Annotated[datetime | None, Query(description="Start time for the query", example="2024-01-01T00:00:00")] = None,
    date_end: Annotated[datetime | None, Query(description="End time for the query", example="2024-01-02T00:00:00")] = None,
    client: Any = Depends(get_clickhouse_dependency),
    user: authenticated_user = None,
) -> APIV4ResponseSchema:
    """
    Get time series data for a specific facility.

    This endpoint returns time series data for a facility, with data grouped by unit.
    The data can be aggregated by different time intervals.

    Args:
        network_code: The network the facility belongs to
        facility_code: The facility code to get data for
        metrics: List of metrics to query (e.g. energy, power, emissions)
        interval: The time interval to aggregate by
        date_start: Start time for the query
        date_end: End time for the query
        client: ClickHouse client dependency

    Returns:
        APIV4ResponseSchema: Time series data response containing a list of TimeSeries objects,
        one per requested metric, with data for each unit
    """
    # Get the network schema
    network = get_api_network_from_code(network_code)

    # validate metrics
    validate_metrics(metrics, _SUPPORTED_METRICS)

    # Validate the date range for the interval
    date_start, date_end = validate_date_range(
        network=network, user=user, interval=interval, date_start=date_start, date_end=date_end
    )

    if facility_code and len(facility_code) > 30:
        raise HTTPException(status_code=400, detail="Facility code must be less than 30 characters")

    # Build and execute query using the unified query builder
    query, params, column_names = get_timeseries_query(
        query_type=QueryType.FACILITY,
        network=network,
        metrics=metrics,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        facility_code=facility_code,
    )

    # Execute query
    try:
        logger.debug(f"Executing query: {query}")
        logger.debug(f"Query params: {params}")
        results = client.execute(query, params)
        logger.debug(f"Query returned {len(results)} rows")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e

    # Check if we got any results
    if not results:
        logger.info(f"No data found for facility {facility_code} in time range {date_start} to {date_end}")
        raise HTTPException(
            status_code=416,
            detail=f"No data available for facility {facility_code} in the specified time range",
        )

    # Convert results to list of dictionaries using column names
    result_dicts = [dict(zip(column_names, row, strict=True)) for row in results]

    # Transform results into response format - returns one TimeSeries per metric
    logger.debug(f"Formatting {len(result_dicts)} results for metrics: {metrics}")
    timeseries_list = format_timeseries_response(
        network=network.code,
        metrics=metrics,
        interval=interval,
        primary_grouping=PrimaryGrouping.NETWORK,  # Not used for facility queries
        secondary_groupings=None,  # Not used for facility queries
        results=result_dicts,
        facility_code=facility_code,
    )
    logger.debug(f"Formatted into {len(timeseries_list)} time series")

    # Debug the response structure
    response_data = APIV4ResponseSchema(data=timeseries_list).model_dump()
    logger.debug(f"Response has {len(response_data.get('data', []))} timeseries objects")
    if response_data.get("data"):
        first_ts = response_data["data"][0]
        logger.debug(f"First timeseries: metric={first_ts.get('metric')}, results_count={len(first_ts.get('results', []))}")
        if first_ts.get("results"):
            first_result = first_ts["results"][0]
            logger.debug(f"First result has {len(first_result.get('data', []))} data points")

    # Return all TimeSeries objects, one per metric
    return ORJSONResponse(response_data)
