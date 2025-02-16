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
from fastapi_versionizer import api_version

from opennem.api.data.queries import get_network_timeseries_query
from opennem.api.data.schema import DataMetric, NetworkTimeSeries, TimeSeriesResult
from opennem.api.data.utils import get_default_start_date, validate_date_range
from opennem.api.schema import APIV4ResponseSchema
from opennem.api.utils import get_api_network_from_code, validate_metrics
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse import get_clickhouse_dependency
from opennem.schema.field_types import SignificantFigures8
from opennem.utils.dates import get_last_completed_interval_for_network

router = APIRouter()

logger = logging.getLogger("opennem.api.data")

_SUPPORTED_METRICS = [
    Metric.ENERGY,
    Metric.POWER,
    Metric.EMISSIONS,
    Metric.MARKET_VALUE,
]


def format_timeseries_response(
    network: str,
    metrics: list[Metric],
    interval: Interval,
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
    results: Sequence[dict[str, Any]],
) -> list[NetworkTimeSeries]:
    """
    Format raw query results into NetworkTimeSeries objects, one per metric.

    Args:
        network: The network code.
        metrics: The list of metrics queried.
        interval: The time interval used.
        primary_grouping: Primary grouping applied.
        secondary_groupings: Secondary groupings applied.
        results: Raw query results from ClickHouse as dictionaries.

    Returns:
        list[NetworkTimeSeries]: List of formatted responses, one per metric.
    """
    # Get min and max dates from results and preserve as datetime objects.
    all_timestamps = [row["interval"] for row in results]
    global_date_start = min(all_timestamps)
    global_date_end = max(all_timestamps)
    dt_start = global_date_start.replace(microsecond=0)
    dt_end = global_date_end.replace(microsecond=0)

    # Combine groupings into a single list (for overall metadata)
    overall_groupings = [primary_grouping.value]
    if secondary_groupings:
        overall_groupings.extend(g.value.lower() for g in secondary_groupings)

    # Build grouping columns list based on primary and secondary grouping.
    group_cols: list[str] = ["network"]

    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        group_cols.append("network_region")

    # Add secondary grouping columns if any
    if secondary_groupings:
        for grouping in secondary_groupings:
            group_cols.append(grouping.value.lower())

    # Group rows based on grouping columns. If no grouping, use default key.
    groups: dict[str, list[dict[str, Any]]] = {}

    logger.debug(f"grouping columns: {group_cols}")
    if group_cols:
        # Grouping key from columns
        for row in results:
            key = tuple(str(row[col]) for col in group_cols)
            groups.setdefault(key, []).append(row)
    else:
        groups["default"] = list(results)

    # Process each metric separately
    network_timeseries_list = []
    for metric in metrics:
        timeseries_results = []

        for group_key, rows in groups.items():
            # Set columns and determine name prefix based on group key
            columns = {}
            name_prefix = f"{network}"
            if group_key != "default":
                # Map column names to their grouping names
                columns = dict(zip(group_cols, group_key, strict=False))
                name_prefix += "_".join(str(val).lower() for val in group_key)

            # Create time series data points for this metric
            data_points: list[tuple[datetime, SignificantFigures8 | None]] = []
            for row in rows:
                timestamp = row["interval"]
                raw_value = row[metric.value.lower()]
                value = float(raw_value) if raw_value is not None else None
                data_points.append((timestamp, value))

            # Sort data points by timestamp (ascending)
            data_points.sort(key=lambda x: x[0])

            # Create time series result for this group
            series_name = f"{name_prefix}_{metric.value}".lower()
            timeseries_results.append(
                TimeSeriesResult(
                    name=series_name,
                    date_start=dt_start,
                    date_end=dt_end,
                    columns=columns,
                    data=data_points,
                )
            )

        # Create NetworkTimeSeries for this metric
        network_data = NetworkTimeSeries(
            network_code=network,
            metric=DataMetric(metric.value),
            interval=interval,
            start=dt_start,
            end=dt_end,
            groupings=overall_groupings,
            results=timeseries_results,
        )
        network_timeseries_list.append(network_data)

    return network_timeseries_list


@api_version(4)
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
        APIV4ResponseSchema: Time series data response containing a list of NetworkTimeSeries objects,
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

    # Build and execute query
    query, params, column_names = get_network_timeseries_query(
        network=network,
        metrics=[DataMetric(m.value) for m in metrics],
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

    # Transform results into response format - returns one NetworkTimeSeries per metric
    network_timeseries_list = format_timeseries_response(
        network=network.code,
        metrics=metrics,
        interval=interval,
        primary_grouping=primary_grouping,
        secondary_groupings=secondary_groupings,
        results=result_dicts,
    )

    # Return all NetworkTimeSeries objects, one per metric
    return APIV4ResponseSchema(data=network_timeseries_list)


@api_version(4)
@router.get("/energy/network/{network_code}/{facility_code}")
async def get_energy_facility(network_code: str, facility_code: str):
    return {"message": "Hello, World!"}
