"""
Market data query functions for OpenNEM API.

This module contains functions for building ClickHouse queries for market data.
"""

from datetime import datetime

from opennem.api.market.schema import MarketMetric
from opennem.core.grouping import PrimaryGrouping
from opennem.core.time_interval import Interval, get_interval_function
from opennem.schema.network import NetworkSchema


def get_market_timeseries_query(
    network: NetworkSchema,
    metrics: list[MarketMetric],
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
    primary_grouping: PrimaryGrouping = PrimaryGrouping.NETWORK,
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
        primary_grouping: Primary grouping to apply (network or network_region)

    Returns:
        tuple[str, dict, list[str]]: ClickHouse SQL query, parameters, and list of column names
    """
    # For 5-minute intervals, use raw base table without time bucket function
    if interval == Interval.INTERVAL:
        time_col = "interval"
        time_fn = time_col
        params = {
            "network": network.code,
            "date_start": date_start,
            "date_end": date_end,
        }
    else:
        # For larger intervals, determine time column and parameters
        if interval.value >= Interval.DAY.value:
            time_col = "date"
            # Convert datetime to date for daily intervals
            params = {
                "network": network.code,
                "date_start": date_start.date(),
                "date_end": date_end.date(),
            }
        else:
            time_col = "interval"
            # Use full datetime for sub-daily intervals
            params = {
                "network": network.code,
                "date_start": date_start,
                "date_end": date_end,
            }
        # Get the time bucket function for the interval
        time_fn = get_interval_function(interval, time_col, database="clickhouse")

    # Map metrics to their column names
    metric_columns = {
        MarketMetric.PRICE: "price",
        MarketMetric.DEMAND: "demand",
        MarketMetric.DEMAND_ENERGY: "demand_energy",
    }

    # Build metric selection part
    metric_selects = [f"avg({metric_columns[m]}) as {m.value.lower()}" for m in metrics]

    # Build grouping columns
    group_cols = ["network_id as network"]
    group_cols_names = ["network"]
    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        group_cols.append("network_region")
        group_cols_names.append("network_region")

    # Build the query
    query = f"""
        SELECT
            {time_fn} as interval,
            {", ".join(group_cols)},
            {", ".join(metric_selects)}
        FROM market_summary
        WHERE
            network_id = %(network)s AND
            {time_col} >= %(date_start)s AND
            {time_col} < %(date_end)s
        GROUP BY
            interval,
            {", ".join([str(i) for i in range(2, len(group_cols) + 2)])}
        ORDER BY
            interval DESC,
            {", ".join([str(i) for i in range(2, len(group_cols) + 2)])}
    """

    # Build list of column names in order
    column_names = ["interval"]
    column_names.extend(group_cols_names)
    column_names.extend(m.value.lower() for m in metrics)

    return query, params, column_names
