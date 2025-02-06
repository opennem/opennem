"""
Database queries for the OpenNEM API v4 data endpoints.

This module contains queries for retrieving energy and related data from
ClickHouse.
"""

from collections.abc import Sequence
from datetime import datetime

from opennem.core.grouping import (
    PrimaryGrouping,
    SecondaryGrouping,
    get_primary_grouping_metadata,
    get_secondary_grouping_metadata,
)
from opennem.core.metric import Metric, get_metric_metadata
from opennem.core.time_interval import Interval, get_interval_function
from opennem.schema.network import NetworkSchema


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

    This query uses the fueltech_intervals_mv materialized view which contains
    pre-aggregated data.

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
        ValueError: If the grouping combination is invalid
    """
    # Get the time bucket function for the interval
    time_fn = get_interval_function(interval, "interval", database="clickhouse")

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

    # Add secondary groupings
    if secondary_groupings:
        for grouping in secondary_groupings:
            meta = get_secondary_grouping_metadata(grouping)
            select_parts.append(f"{meta.column_name}")
            group_by_parts.append(meta.column_name)

    # Add the metric value
    select_parts.append(f"{metric_meta.default_agg}({metric_meta.column_name}) as value")

    # Build the query
    query = f"""
    SELECT
        {", ".join(select_parts)}
    FROM fueltech_intervals_mv
    WHERE
        network_id = %(network_id)s AND
        interval >= %(date_start)s AND
        interval < %(date_end)s
    GROUP BY
        {", ".join(group_by_parts)}
    ORDER BY
        interval DESC
    """

    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        query += ", network_region ASC"

    if secondary_groupings:
        for grouping in secondary_groupings:
            meta = get_secondary_grouping_metadata(grouping)
            query += f", {meta.column_name} ASC"

    params = {
        "network_id": network.code,
        "date_start": date_start,
        "date_end": date_end,
    }

    return query, params
