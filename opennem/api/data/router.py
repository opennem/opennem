"""
Data router for the OpenNEM API v4.

This module provides endpoints for accessing energy data at various granularities
and aggregation levels.
"""

import logging
from datetime import datetime
from typing import Annotated

from clickhouse_driver.client import Client
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_versionizer import api_version

from opennem.api.data.queries import get_network_timeseries_query
from opennem.api.data.schema import NetworkTimeSeries, NetworkTimeSeriesResponse, TimeSeriesResult
from opennem.api.utils import get_api_network_from_code, get_default_period_for_interval
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import get_clickhouse_client
from opennem.utils.dates import get_last_completed_interval_for_network

router = APIRouter()

logger = logging.getLogger("opennem.api.data")


def _group_rows_by_column(rows, column_index: int) -> dict[str, list]:
    """
    Group rows by a specific column value.

    Args:
        rows: List of database rows
        column_index: Index of the column to group by

    Returns:
        dict: Mapping of column values to lists of rows
    """
    result = {}
    for row in rows:
        key = row[column_index] if len(row) > column_index else None
        if key is not None:
            if key not in result:
                result[key] = []
            result[key].append(row)
    return result


@api_version(4)
@router.get(
    "/energy/network/{network_code}",
    response_model=NetworkTimeSeriesResponse,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
async def get_energy_network(
    network_code: str,
    interval: Annotated[Interval, Query(description="The time interval to aggregate data by", example="1h")] = Interval.INTERVAL,
    date_start: Annotated[
        datetime | None, Query(description="Start time for the query (UTC)", example="2024-01-01T00:00:00Z")
    ] = None,
    date_end: Annotated[
        datetime | None, Query(description="End time for the query (UTC)", example="2024-01-02T00:00:00Z")
    ] = None,
    primary_grouping: Annotated[
        PrimaryGrouping, Query(description="Primary grouping to apply", example="network_region")
    ] = PrimaryGrouping.NETWORK,
    secondary_grouping: Annotated[
        SecondaryGrouping | None, Query(description="Optional secondary grouping to apply", example="fueltech_group")
    ] = None,
    client: Client = Depends(get_clickhouse_client),
) -> NetworkTimeSeriesResponse:
    """
    Get energy data for a specific network.

    This endpoint returns energy data for a network, optionally filtered by
    time interval and date range. Data is aggregated according to the specified
    groupings.

    Args:
        network_code: The network code to get data for
        interval: The time interval to aggregate by
        date_start: Start time for the query (UTC)
        date_end: End time for the query (UTC)
        primary_grouping: Primary grouping to apply (network or network_region)
        secondary_grouping: Optional secondary grouping to apply
        client: ClickHouse client

    Returns:
        NetworkTimeSeriesResponse: The energy data response

    Raises:
        HTTPException: If the network is not found or parameters are invalid
    """
    # Validate network exists
    network = get_api_network_from_code(network_code)

    # Set default time range if not provided
    if not date_end:
        date_end = get_last_completed_interval_for_network(network=network, tz_aware=False)

    if not date_start:
        date_start = date_end - get_default_period_for_interval(interval)

    # Validate time range
    if date_start >= date_end:
        raise HTTPException(status_code=400, detail="Start time must be before end time")

    # Get the energy data
    query, params = get_network_timeseries_query(
        network=network,
        metric=Metric.ENERGY,
        interval=interval,
        date_start=date_start,
        date_end=date_end,
        primary_grouping=primary_grouping,
        secondary_groupings=[secondary_grouping] if secondary_grouping else None,
    )
    logger.info(query)
    rows = client.execute(query, params)

    # Create time series results
    results = []

    if primary_grouping == PrimaryGrouping.NETWORK:
        # Single result for the whole network
        if secondary_grouping:
            # Group by secondary grouping
            for group_id, group_rows in _group_rows_by_column(rows, 1).items():
                results.append(
                    TimeSeriesResult(
                        name=group_id,
                        date_start=date_start,
                        date_end=date_end,
                        labels={secondary_grouping: group_id},
                        data=[(row[0], float(row[-1]) if row[-1] is not None else None) for row in group_rows],
                    )
                )
        else:
            # No grouping, just network total
            results.append(
                TimeSeriesResult(
                    name=network_code,
                    date_start=date_start,
                    date_end=date_end,
                    data=[(row[0], float(row[-1]) if row[-1] is not None else None) for row in rows],
                )
            )
    else:  # NETWORK_REGION
        # Group by region first
        for region_id, region_rows in _group_rows_by_column(rows, 1).items():
            if secondary_grouping:
                # Then by secondary grouping
                for group_id, group_rows in _group_rows_by_column(region_rows, 2).items():
                    results.append(
                        TimeSeriesResult(
                            name=f"{region_id}_{group_id}",
                            date_start=date_start,
                            date_end=date_end,
                            labels={"region": region_id, secondary_grouping: group_id},
                            data=[(row[0], float(row[-1]) if row[-1] is not None else None) for row in group_rows],
                        )
                    )
            else:
                # Just regional totals
                results.append(
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
        network_code=network_code,
        metric=Metric.ENERGY,
        interval=interval,
        start=date_start,
        end=date_end,
        primary_grouping=primary_grouping,
        secondary_groupings=[secondary_grouping] if secondary_grouping else [],
        results=results,
    )

    return NetworkTimeSeriesResponse(data=network_data)


@api_version(4)
@router.get("/energy/network/{network_code}/{facility_code}")
async def get_energy_facility(network_code: str, facility_code: str):
    return {"message": "Hello, World!"}
