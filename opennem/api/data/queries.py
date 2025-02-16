"""
Database queries for the OpenNEM API v4 data endpoints.

This module contains queries for retrieving energy and related data from
ClickHouse.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import NoReturn

from fastapi import HTTPException

from opennem.api.data.schema import DataMetric
from opennem.core.grouping import (
    PrimaryGrouping,
    SecondaryGrouping,
)
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
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

    # Check if we're grouping by renewable status
    if secondary_groupings and SecondaryGrouping.RENEWABLE in secondary_groupings:
        if interval in (Interval.INTERVAL, Interval.HOUR):
            return "renewable_intervals_mv"
        else:
            return "renewable_intervals_daily_mv"

    # For other metrics and groupings, select based on interval size
    if interval in (Interval.INTERVAL, Interval.HOUR):
        return "unit_intervals"
    elif interval in (Interval.DAY, Interval.WEEK):
        return "unit_intervals_daily_mv"
    else:
        return "unit_intervals_monthly_mv"


def get_network_timeseries_query(
    network: NetworkSchema,
    metrics: list[DataMetric],
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
    primary_grouping: PrimaryGrouping,
    secondary_groupings: Sequence[SecondaryGrouping] | None,
) -> tuple[str, dict, list[str]]:
    """
    Get time series data for market metrics.

    This query selects from the market_summary table and supports multiple
    metrics in a single query.

    Args:
        network: The network to get data for
        metrics: List of metrics to query
        interval: The time interval to aggregate by
        date_start: Start time for the query (network time)
        date_end: End time for the query (network time)
        primary_grouping: Primary grouping to apply
        secondary_groupings: Optional sequence of secondary groupings to apply

    Returns:
        tuple[str, dict, list[str]]: ClickHouse SQL query, parameters, and list of column names
    """
    # Map metrics to their column names
    metric_columns = {
        DataMetric.POWER: "generated",
        DataMetric.ENERGY: "energy",
        DataMetric.EMISSIONS: "emissions",
        DataMetric.MARKET_VALUE: "market_value",
    }

    # Build metric selection part
    metric_selects = [f"sum({metric_columns[m]}) as {m.value.lower()}" for m in metrics]

    # Build grouping columns
    group_cols = []
    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        group_cols.append("network_region")
    elif primary_grouping == PrimaryGrouping.NETWORK and secondary_groupings:
        for grouping in secondary_groupings:
            if grouping == SecondaryGrouping.RENEWABLE:
                group_cols.append("renewable")
            elif grouping == SecondaryGrouping.FUELTECH:
                group_cols.append("fueltech_id")
            elif grouping == SecondaryGrouping.FUELTECH_GROUP:
                group_cols.append("fueltech_group_id")

    # Build the query
    query = f"""
        SELECT
            interval as interval,
            {", ".join(group_cols) if group_cols else "network_id"},
            {", ".join(metric_selects)}
        FROM unit_intervals
        WHERE
            network_id = %(network)s AND
            interval >= %(date_start)s AND
            interval < %(date_end)s
        GROUP BY
            interval,
            {", ".join(group_cols) if group_cols else "network_id"}
        ORDER BY
            interval DESC,
            {", ".join(group_cols) if group_cols else "network_id"} ASC
    """

    params = {
        "network": network.code,
        "date_start": date_start,
        "date_end": date_end,
    }

    # Build list of column names in order
    column_names = ["interval"]
    if group_cols:
        column_names.extend(group_cols)
    else:
        column_names.append("network_id")
    column_names.extend(m.value.lower() for m in metrics)

    return query, params, column_names
