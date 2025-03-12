"""
Unified query builder for OpenNEM API time series data.

This module provides a common interface for building time series queries
for both market and data endpoints.
"""

import logging
from datetime import datetime
from enum import Enum

from opennem.api.data.schema import DataMetric
from opennem.api.market.schema import MarketMetric
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.time_interval import Interval, get_interval_function
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.api.queries")

# Type alias for metrics that can be either market or data metrics
type MetricType = DataMetric | MarketMetric


class QueryType(str, Enum):
    """Type of query to build."""

    MARKET = "market"
    DATA = "data"
    FACILITY = "facility"


class QueryConfig:
    """Configuration for building a time series query."""

    def __init__(
        self,
        query_type: QueryType,
        base_table: str,
        daily_mv: str | None,
        monthly_mv: str | None,
        metric_columns: dict[MetricType, str],
        metric_agg_functions: dict[MetricType, str],
    ):
        """
        Initialize query configuration.

        Args:
            query_type: Type of query (market or data)
            base_table: Name of the base table to query
            daily_mv: Name of daily materialized view (if available)
            monthly_mv: Name of monthly materialized view (if available)
            metric_columns: Mapping of metrics to their column names
            metric_agg_functions: Mapping of metrics to their aggregation functions
        """
        self.query_type = query_type
        self.base_table = base_table
        self.daily_mv = daily_mv
        self.monthly_mv = monthly_mv
        self.metric_columns = metric_columns
        self.metric_agg_functions = metric_agg_functions

    def _get_table_for_interval(self, interval: Interval) -> str:
        """
        Get the appropriate table or materialized view for the interval.

        Args:
            config: Query configuration
            interval: Time interval

        Returns:
            str: Table or view name to query from
        """
        if interval in [Interval.INTERVAL, Interval.HOUR]:
            return self.base_table
        else:
            return self.daily_mv or self.base_table

    def _get_time_column(self, interval: Interval) -> str:
        """
        Get the appropriate time column for the interval.
        """
        if not self.daily_mv and not self.monthly_mv:
            return "interval"

        if interval in [Interval.INTERVAL, Interval.HOUR]:
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
        metric_agg_functions={
            MarketMetric.PRICE: "avg",
            MarketMetric.DEMAND: "avg",
            MarketMetric.DEMAND_ENERGY: "sum",
        },
    ),
    QueryType.DATA: QueryConfig(
        query_type=QueryType.DATA,
        base_table="unit_intervals",
        daily_mv="unit_intervals_daily_mv",
        monthly_mv=None,
        metric_columns={
            DataMetric.POWER: "generated",
            DataMetric.ENERGY: "energy",
            DataMetric.EMISSIONS: "emissions",
            DataMetric.MARKET_VALUE: "market_value",
        },
        metric_agg_functions={
            DataMetric.POWER: "sum",
            DataMetric.ENERGY: "sum",
            DataMetric.EMISSIONS: "sum",
            DataMetric.MARKET_VALUE: "sum",
        },
    ),
    QueryType.FACILITY: QueryConfig(
        query_type=QueryType.FACILITY,
        base_table="unit_intervals",
        daily_mv="unit_intervals_daily_mv",
        monthly_mv=None,
        metric_columns={
            DataMetric.POWER: "generated",
            DataMetric.ENERGY: "energy",
            DataMetric.EMISSIONS: "emissions",
            DataMetric.MARKET_VALUE: "market_value",
        },
        metric_agg_functions={
            DataMetric.POWER: "sum",
            DataMetric.ENERGY: "sum",
            DataMetric.EMISSIONS: "sum",
            DataMetric.MARKET_VALUE: "sum",
        },
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
    # filters
    facility_code: list[str] | None = None,
    network_region: str | None = None,
    fueltech: str | None = None,
    fueltech_group: str | None = None,
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
        facility_code: Optional facility codes to filter by
        network_region: Optional network region to filter by
        fueltech: Optional fueltech to filter by
        fueltech_group: Optional fueltech group to filter by

    Returns:
        tuple[str, dict, list[str]]: ClickHouse SQL query, parameters, and list of column names
    """
    config = QUERY_CONFIGS[query_type]

    # Determine which table/view to use based on interval
    table_name = config._get_table_for_interval(interval)
    time_col = config._get_time_column(interval)
    time_fn = get_interval_function(interval, time_col, database="clickhouse")

    # Convert date range to network time if interval is daily or longer
    if interval in [
        Interval.DAY,
        Interval.WEEK,
        Interval.MONTH,
        Interval.QUARTER,
        Interval.YEAR,
        Interval.SEASON,
        Interval.FINANCIAL_YEAR,
    ]:
        date_start = date_start.date()
        date_end = date_end.date()

    params = {
        "network": network.get_network_codes(),
        "date_start": date_start,
        "date_end": date_end,
    }

    # logger.info(f"Querying {table_name} for {network.code} from {date_start} to {date_end}")

    # Build metric selection part
    metric_selects = [f"{config.metric_agg_functions[m]}({config.metric_columns[m]}) as {m.value.lower()}" for m in metrics]

    # Build grouping columns based on query type
    group_cols = [f"'{network.code}' as network"]
    group_cols_names = ["network"]

    if query_type == QueryType.FACILITY:
        group_cols.extend(["facility_code", "unit_code"])
        group_cols_names.extend(["facility_code", "unit_code"])
        params["facility_code"] = facility_code
    elif primary_grouping == PrimaryGrouping.NETWORK_REGION:
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

    # Build the query with facility filter if provided
    where_clauses = [
        "network_id in %(network)s",
        f"{time_col} >= %(date_start)s",
        f"{time_col} < %(date_end)s",
    ]

    if facility_code:
        where_clauses.append("facility_code in %(facility_code)s")
        params["facility_code"] = facility_code

    if network_region:
        where_clauses.append("network_region = %(network_region)s")
        params["network_region"] = network_region

    if fueltech:
        where_clauses.append("fueltech_id = %(fueltech)s")
        params["fueltech"] = fueltech

    if fueltech_group:
        where_clauses.append("fueltech_group_id = %(fueltech_group)s")
        params["fueltech_group"] = fueltech_group

    query = f"""
        SELECT
            {time_fn} as interval,
            {", ".join(group_cols)},
            {", ".join(metric_selects)}
        FROM {table_name}
        WHERE {" AND ".join(where_clauses)}
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
