"""
Database queries for the OpenNEM API v4 data endpoints.

This module contains queries for retrieving energy and related data from
ClickHouse.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import NoReturn

from fastapi import HTTPException

from opennem.core.grouping import (
    PrimaryGrouping,
    SecondaryGrouping,
    get_primary_grouping_metadata,
    get_secondary_grouping_metadata,
)
from opennem.core.metric import Metric, get_metric_metadata
from opennem.core.time_interval import Interval, get_interval_function
from opennem.db.clickhouse_views import CLICKHOUSE_MATERIALIZED_VIEWS
from opennem.schema.network import NetworkSchema


def _raise_unsupported_grouping(metric: Metric) -> NoReturn:
    """
    Raise an HTTP error for unsupported groupings.

    Args:
        metric: The metric that doesn't support grouping

    Raises:
        HTTPException: Always raised with a descriptive message
    """
    raise HTTPException(
        status_code=400, detail=f"Secondary groupings are not supported for {metric} as it is a market-level metric"
    )


def _get_source_table(metric: Metric, interval: Interval, secondary_groupings: Sequence[SecondaryGrouping] | None = None) -> str:
    """
    Get the appropriate source table or materialized view based on metric and interval.

    Args:
        metric: The metric being queried
        interval: The time interval for aggregation
        secondary_groupings: Optional sequence of secondary groupings

    Returns:
        str: The name of the table or view to query from

    Raises:
        HTTPException: If secondary groupings are used with market metrics
    """
    # Market metrics use market_summary table and don't support secondary groupings
    if metric in (Metric.DEMAND, Metric.DEMAND_ENERGY, Metric.PRICE):
        if secondary_groupings:
            _raise_unsupported_grouping(metric)
        return "market_summary"

    # For other metrics, select based on interval size
    if interval in (Interval.INTERVAL, Interval.HOUR):
        return "unit_intervals"
    elif interval in (Interval.DAY, Interval.WEEK):
        return "unit_intervals_daily_mv"
    else:
        return "unit_intervals_monthly_mv"


def get_network_timeseries_query(
    network: NetworkSchema,
    metric: Metric,
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
    primary_grouping: PrimaryGrouping = PrimaryGrouping.NETWORK,
    secondary_groupings: Sequence[SecondaryGrouping] | None = None,
) -> tuple[str, dict]:
    """
    Get time series data for a network.

    This query selects from the appropriate table or materialized view based on
    the metric and interval size requested.

    Args:
        network: The network to get data for
        metric: The metric to query
        interval: The time interval to aggregate by
        date_start: Start time for the query (network time)
        date_end: End time for the query (network time)
        primary_grouping: The primary grouping to apply (network or network_region)
        secondary_groupings: Optional sequence of secondary groupings to apply

    Returns:
        tuple[str, dict]: ClickHouse SQL query and parameters

    Raises:
        HTTPException: If the grouping combination is invalid or unsupported for the metric
    """
    # Get the source table based on metric and interval
    source_table = _get_source_table(metric, interval, secondary_groupings)

    # Get the timestamp column name based on the source table
    # - Raw tables use 'interval'
    # - Materialized views use 'date'
    timestamp_col = "interval"

    if source_table in CLICKHOUSE_MATERIALIZED_VIEWS:
        timestamp_col = CLICKHOUSE_MATERIALIZED_VIEWS[source_table].timestamp_column

    # Get the time bucket function for the interval
    time_fn = get_interval_function(interval, timestamp_col, database="clickhouse")

    # Get the metric metadata
    metric_meta = get_metric_metadata(metric)

    # Build the select clause
    select_parts = [
        f"{time_fn} as interval",
    ]

    # Add primary grouping
    group_by_parts = ["interval"]
    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        primary_meta = get_primary_grouping_metadata(primary_grouping)
        select_parts.append(f"{primary_meta.column_name}")
        group_by_parts.append(primary_meta.column_name)

    # Add secondary groupings for non-market metrics
    if secondary_groupings and source_table != "market_summary":
        for grouping in secondary_groupings:
            meta = get_secondary_grouping_metadata(grouping)
            select_parts.append(f"{meta.column_name}")
            group_by_parts.append(meta.column_name)

    # Add the metric value - handle special cases for market metrics
    select_parts.append(f"{metric_meta.default_agg}({metric_meta.column_name}) as value")

    # For intervals of a day or greater, convert datetime to date
    query_date_start = date_start
    query_date_end = date_end

    if interval in (Interval.DAY, Interval.WEEK, Interval.MONTH, Interval.QUARTER, Interval.YEAR, Interval.FINANCIAL_YEAR):
        query_date_start = date_start.date()
        query_date_end = date_end.date()

    # Build the query
    query = f"""
    SELECT
        {", ".join(select_parts)}
    FROM {source_table}
    WHERE
        network_id = %(network_id)s AND
        {timestamp_col} >= %(date_start)s AND
        {timestamp_col} < %(date_end)s
    GROUP BY
        {", ".join(group_by_parts)}
    ORDER BY
        interval DESC
    """

    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        query += ", network_region ASC"

    if secondary_groupings and source_table != "market_summary":
        for grouping in secondary_groupings:
            meta = get_secondary_grouping_metadata(grouping)
            query += f", {meta.column_name} ASC"

    params = {
        "network_id": network.code,
        "date_start": query_date_start,
        "date_end": query_date_end,
    }

    return query, params
