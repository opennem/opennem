"""
Unified query builder for OpenNEM API time series data.

This module provides a common interface for building time series queries
for both market and data endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from opennem.api.data.schema import DataMetric
from opennem.api.market.schema import MarketMetric
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.time_interval import Interval, get_interval_function
from opennem.schema.network import NetworkSchema

# Type alias for metrics that can be either market or data metrics
type MetricType = DataMetric | MarketMetric


class QueryType(str, Enum):
    """Type of query to build."""

    MARKET = "market"
    DATA = "data"


class QueryConfig:
    """Configuration for building a time series query."""

    def __init__(
        self,
        query_type: QueryType,
        base_table: str,
        daily_mv: str | None,
        monthly_mv: str | None,
        metric_columns: dict[Any, str],
        agg_function: str = "avg",
    ):
        """
        Initialize query configuration.

        Args:
            query_type: Type of query (market or data)
            base_table: Name of the base table to query
            daily_mv: Name of daily materialized view (if available)
            monthly_mv: Name of monthly materialized view (if available)
            metric_columns: Mapping of metrics to their column names
            agg_function: Aggregation function to use (default: avg)
        """
        self.query_type = query_type
        self.base_table = base_table
        self.daily_mv = daily_mv
        self.monthly_mv = monthly_mv
        self.metric_columns = metric_columns
        self.agg_function = agg_function

    def _get_table_for_interval(self, interval: Interval) -> str:
        """
        Get the appropriate table or materialized view for the interval.

        Args:
            config: Query configuration
            interval: Time interval

        Returns:
            str: Table or view name to query from
        """
        if interval == Interval.INTERVAL:
            return self.base_table
        elif interval in [Interval.MONTH, Interval.QUARTER, Interval.YEAR]:
            return self.monthly_mv or self.base_table
        else:
            return self.daily_mv or self.base_table

    def _get_time_column(self, interval: Interval) -> str:
        """
        Get the appropriate time column for the interval.
        """
        if not self.daily_mv and not self.monthly_mv:
            return "interval"

        if interval == Interval.INTERVAL:
            return "interval"
        return "date"


# Query configurations for different types
QUERY_CONFIGS = {
    QueryType.MARKET: QueryConfig(
        query_type=QueryType.MARKET,
        base_table="market_summary",
        daily_mv=None,  # Will be added when market summary MVs are created
        monthly_mv=None,  # Will be added when market summary MVs are created
        metric_columns={
            MarketMetric.PRICE: "price",
            MarketMetric.DEMAND: "demand",
            MarketMetric.DEMAND_ENERGY: "demand_energy",
        },
        agg_function="avg",
    ),
    QueryType.DATA: QueryConfig(
        query_type=QueryType.DATA,
        base_table="unit_intervals",
        daily_mv="unit_intervals_daily_mv",
        monthly_mv="unit_intervals_monthly_mv",
        metric_columns={
            DataMetric.POWER: "generated",
            DataMetric.ENERGY: "energy",
            DataMetric.EMISSIONS: "emissions",
            DataMetric.MARKET_VALUE: "market_value",
        },
        agg_function="sum",
    ),
}


def get_timeseries_query(
    query_type: QueryType,
    network: NetworkSchema,
    metrics: list[MetricType],
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
    primary_grouping: PrimaryGrouping = PrimaryGrouping.NETWORK,
    secondary_groupings: list[SecondaryGrouping] | None = None,
) -> tuple[str, dict, list[str]]:
    """
    Build a time series query for either market or data metrics.

    Args:
        query_type: Type of query to build (market or data)
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
    config = QUERY_CONFIGS[query_type]

    # Determine which table/view to use based on interval
    table_name = config._get_table_for_interval(interval)
    time_col = config._get_time_column(interval)
    time_fn = get_interval_function(interval, time_col, database="clickhouse")

    if time_col != "interval":
        date_start = date_start.date()
        date_end = date_end.date()

    params = {
        "network": network.code,
        "date_start": date_start,
        "date_end": date_end,
    }

    # Build metric selection part
    metric_selects = [f"{config.agg_function}({config.metric_columns[m]}) as {m.value.lower()}" for m in metrics]

    # Build grouping columns
    group_cols = ["network_id as network"]
    group_cols_names = ["network"]
    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        group_cols.append("network_region")
        group_cols_names.append("network_region")

    # Add secondary grouping columns if supported and provided
    if query_type == QueryType.DATA and secondary_groupings:
        for grouping in secondary_groupings:
            if grouping == SecondaryGrouping.RENEWABLE:
                group_cols.append("renewable")
                group_cols_names.append("renewable")
            elif grouping == SecondaryGrouping.FUELTECH:
                group_cols.append("fueltech_id")
                group_cols_names.append("fueltech")
            elif grouping == SecondaryGrouping.FUELTECH_GROUP:
                group_cols.append("fueltech_group_id")
                group_cols_names.append("fueltech_group")

    # Build the query
    query = f"""
        SELECT
            {time_fn} as interval,
            {", ".join(group_cols)},
            {", ".join(metric_selects)}
        FROM {table_name}
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
