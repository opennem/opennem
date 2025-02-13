"""
API router for OpenNEM data endpoints.

This module contains the FastAPI router for data endpoints, including time series
data queries.
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.params import Path
from fastapi_versionizer import api_version

from opennem.api.data.queries import get_network_timeseries_query
from opennem.api.data.schema import NetworkTimeSeries, NetworkTimeSeriesResponse, TimeSeriesResult
from opennem.api.data.utils import get_default_start_date, validate_date_range
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import Client, get_clickhouse_client
from opennem.utils.dates import get_last_completed_interval_for_network

router = APIRouter()

logger = logging.getLogger("opennem.api.data")


def _group_rows_by_column(rows: Sequence[Any], col_idx: int) -> dict[str, list[Any]]:
    """
    Group rows by a specific column value.

    Args:
        rows: Sequence of rows to group
        col_idx: Index of column to group by

    Returns:
        dict: Grouped rows with column value as key
    """
    groups: dict[str, list[Any]] = {}
    for row in rows:
        key = row[col_idx]
        if key not in groups:
            groups[key] = []
        groups[key].append(row)
    return groups


def format_timeseries_response(
    network: str,
    metric: Metric,
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
    results: Sequence[Any],
) -> NetworkTimeSeriesResponse:
    """
    Format raw query results into a NetworkTimeSeriesResponse.

    Args:
        network: The network code
        metric: The metric queried
        interval: The time interval used
        date_start: Start time of the query
        date_end: End time of the query
        primary_grouping: Primary grouping applied
        secondary_groupings: Secondary groupings applied
        results: Raw query results

    Returns:
        NetworkTimeSeriesResponse: Formatted response
    """
    timeseries_results = []

    if primary_grouping == PrimaryGrouping.NETWORK:
        # Single result for the whole network
        if secondary_groupings:
            # Group by secondary grouping
            for group_id, group_rows in _group_rows_by_column(results, 1).items():
                timeseries_results.append(
                    TimeSeriesResult(
                        name=group_id,
                        date_start=date_start,
                        date_end=date_end,
                        labels={secondary_groupings[0]: group_id},
                        data=[(row[0], float(row[-1]) if row[-1] is not None else None) for row in group_rows],
                    )
                )
        else:
            # No grouping, just network total
            timeseries_results.append(
                TimeSeriesResult(
                    name=network,
                    date_start=date_start,
                    date_end=date_end,
                    data=[(row[0], float(row[-1]) if row[-1] is not None else None) for row in results],
                )
            )
    else:  # NETWORK_REGION
        # Group by region first
        for region_id, region_rows in _group_rows_by_column(results, 1).items():
            if secondary_groupings:
                # Then by secondary grouping
                for group_id, group_rows in _group_rows_by_column(region_rows, 2).items():
                    timeseries_results.append(
                        TimeSeriesResult(
                            name=f"{region_id}_{group_id}",
                            date_start=date_start,
                            date_end=date_end,
                            labels={"region": region_id, secondary_groupings[0]: group_id},
                            data=[(row[0], float(row[-1]) if row[-1] is not None else None) for row in group_rows],
                        )
                    )
            else:
                # Just regional totals
                timeseries_results.append(
                    TimeSeriesResult(
                        name=region_id,
                        date_start=date_start,
                        date_end=date_end,
                        labels={"region": region_id},
                        data=[(row[0], float(row[-1]) if row[-1] is not None else None) for row in region_rows],
                    )
                )

    # Create the response data
    network_data = NetworkTimeSeries(
        network_code=network,
        metric=metric,
        interval=interval,
        start=date_start,
        end=date_end,
        primary_grouping=primary_grouping,
        secondary_groupings=secondary_groupings or [],
        results=timeseries_results,
    )

    return NetworkTimeSeriesResponse(data=network_data)


@api_version(4)
@router.get(
    "/network/{network_code}/{metric}",
    response_model=NetworkTimeSeriesResponse,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
async def get_network_data(
    network_code: str,
    metric: Annotated[Metric, Path(description="The metric to get data for", example="energy")],
    interval: Annotated[Interval, Query(description="The time interval to aggregate data by", example="1h")] = Interval.INTERVAL,
    date_start: Annotated[datetime | None, Query(description="Start time for the query", example="2024-01-01T00:00:00")] = None,
    date_end: Annotated[datetime | None, Query(description="End time for the query", example="2024-01-02T00:00:00")] = None,
    primary_grouping: Annotated[
        PrimaryGrouping, Query(description="Primary grouping to apply", example="network_region")
    ] = PrimaryGrouping.NETWORK,
    secondary_grouping: Annotated[
        SecondaryGrouping | None, Query(description="Optional secondary grouping to apply", example="fueltech_group")
    ] = None,
    client: Client = Depends(get_clickhouse_client),
) -> NetworkTimeSeriesResponse:
    """
    Get time series data for a network.

    This endpoint returns time series data for a network, with optional grouping
    by region and other dimensions. The data can be aggregated by different time
    intervals.

    Args:
        network_code: The network to get data for
        metric: The metric to query (e.g. energy, power, price)
        interval: The time interval to aggregate by
        date_start: Start time for the query
        date_end: End time for the query
        primary_grouping: Primary grouping to apply
        secondary_grouping: Optional secondary grouping to apply
        client: ClickHouse client dependency

    Returns:
        NetworkTimeSeriesResponse: Time series data response

    Raises:
        HTTPException: If the date range is too large for the interval
    """
    # check metrics that don't support secondary groupings
    if metric in (Metric.DEMAND, Metric.DEMAND_ENERGY, Metric.PRICE, Metric.EMISSIONS, Metric.MARKET_VALUE):
        secondary_grouping = None

    # Get the network schema
    network = get_api_network_from_code(network_code)

    # Get default dates if not provided
    if date_end is None:
        date_end = get_last_completed_interval_for_network(network=network)

    if date_start is None:
        date_start = get_default_start_date(interval, date_end)

    # Validate the date range for the interval
    validate_date_range(interval, date_start, date_end)

    # Convert single secondary grouping to sequence
    secondary_groupings = [secondary_grouping] if secondary_grouping else None

    # Build and execute query
    query, params = get_network_timeseries_query(
        network=network,
        metric=metric,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping=primary_grouping,
        secondary_groupings=secondary_groupings,
    )

    # Execute query
    try:
        results = client.execute(query, params)
        logger.debug(query)
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Error executing query") from e

    # Transform results into response format
    response = format_timeseries_response(
        network=network.code,
        metric=metric,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping=primary_grouping,
        secondary_groupings=secondary_groupings,
        results=results,
    )

    return response


@api_version(4)
@router.get("/energy/network/{network_code}/{facility_code}")
async def get_energy_facility(network_code: str, facility_code: str):
    return {"message": "Hello, World!"}
