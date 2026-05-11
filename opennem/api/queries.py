"""
Unified query builder for OpenNEM API time series data.

This module provides a common interface for building time series queries
for both market and data endpoints.
"""

import logging
from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum

from opennem.api.data.schema import DataMetric
from opennem.api.market.schema import MarketMetric
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval, get_interval_function
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.api.queries")

# Type alias for metrics that can be either market or data metrics
type MetricType = DataMetric | MarketMetric | Metric


class QueryType(StrEnum):
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
        daily_metric_columns: dict[MetricType, str] | None = None,
        daily_metric_agg_functions: dict[MetricType, str] | None = None,
    ):
        self.query_type = query_type
        self.base_table = base_table
        self.daily_mv = daily_mv
        self.monthly_mv = monthly_mv
        self.metric_columns = metric_columns
        self.metric_agg_functions = metric_agg_functions
        self.daily_metric_columns = daily_metric_columns
        self.daily_metric_agg_functions = daily_metric_agg_functions

    def get_metric_column(self, metric: MetricType, table: str) -> str:
        if table == self.daily_mv and self.daily_metric_columns and metric in self.daily_metric_columns:
            return self.daily_metric_columns[metric]
        return self.metric_columns[metric]

    def get_metric_agg(self, metric: MetricType, table: str) -> str:
        if table == self.daily_mv and self.daily_metric_agg_functions and metric in self.daily_metric_agg_functions:
            return self.daily_metric_agg_functions[metric]
        return self.metric_agg_functions[metric]

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
        daily_mv="market_summary_daily_mv",
        monthly_mv="market_summary_monthly_mv",
        metric_columns={
            Metric.PRICE: "price",
            Metric.DEMAND: "demand",
            Metric.DEMAND_ENERGY: "demand_energy",
            Metric.DEMAND_GROSS: "demand_gross",
            Metric.DEMAND_GROSS_ENERGY: "demand_gross_energy",
            Metric.GENERATION_RENEWABLE: "generation_renewable",
            Metric.GENERATION_RENEWABLE_ENERGY: "generation_renewable_energy",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE: "generation_renewable_with_storage",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY: "generation_renewable_with_storage_energy",
            Metric.CURTAILMENT: "curtailment_total",
            Metric.CURTAILMENT_ENERGY: "curtailment_energy_total",
            Metric.CURTAILMENT_SOLAR_UTILITY: "curtailment_solar_total",
            Metric.CURTAILMENT_WIND: "curtailment_wind_total",
            Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY: "curtailment_energy_solar_total",
            Metric.CURTAILMENT_WIND_ENERGY: "curtailment_energy_wind_total",
            Metric.RENEWABLE_PROPORTION: "round(if(sum(demand_gross) > 0, (sum(generation_renewable) / sum(demand_gross)) * 100, 0), 2)",  # noqa: E501
            Metric.RENEWABLE_WITH_STORAGE_PROPORTION: "round(if(sum(demand_gross) > 0, (sum(generation_renewable_with_storage) / sum(demand_gross)) * 100, 0), 2)",  # noqa: E501
            Metric.FLOW_IMPORTS: "energy_imports * 12",  # MWh to MW
            Metric.FLOW_EXPORTS: "energy_exports * 12",
            Metric.FLOW_IMPORTS_ENERGY: "energy_imports",
            Metric.FLOW_EXPORTS_ENERGY: "energy_exports",
        },
        # KNOWN BUG: MW metrics (demand, demand_gross, generation_renewable*, curtailment*,
        # flow_imports/exports) are summed across intervals when they should be averaged — same
        # class of bug as opennem#523, but switching to avg trips a ClickHouse analyzer
        # limitation when the same SELECT also returns renewable_proportion (mixes avg(x) and
        # sum(x) on the same column). Fix needs a CTE/subquery restructure of the query builder.
        # Tracked separately.
        metric_agg_functions={
            Metric.PRICE: "avg",
            Metric.DEMAND: "sum",
            Metric.DEMAND_ENERGY: "sum",
            Metric.DEMAND_GROSS: "sum",
            Metric.DEMAND_GROSS_ENERGY: "sum",
            Metric.GENERATION_RENEWABLE: "sum",
            Metric.GENERATION_RENEWABLE_ENERGY: "sum",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE: "sum",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY: "sum",
            Metric.CURTAILMENT: "sum",
            Metric.CURTAILMENT_ENERGY: "sum",
            Metric.CURTAILMENT_SOLAR_UTILITY: "sum",
            Metric.CURTAILMENT_WIND: "sum",
            Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY: "sum",
            Metric.CURTAILMENT_WIND_ENERGY: "sum",
            Metric.RENEWABLE_PROPORTION: "",
            Metric.RENEWABLE_WITH_STORAGE_PROPORTION: "",
            Metric.FLOW_IMPORTS: "sum",
            Metric.FLOW_EXPORTS: "sum",
            Metric.FLOW_IMPORTS_ENERGY: "sum",
            Metric.FLOW_EXPORTS_ENERGY: "sum",
        },
        daily_metric_columns={
            Metric.PRICE: "round(sum(price_sum) / nullIf(sum(price_count), 0), 6)",
            Metric.DEMAND: "demand_sum",
            Metric.DEMAND_ENERGY: "demand_energy_daily",
            Metric.DEMAND_GROSS: "demand_gross_sum",
            Metric.DEMAND_GROSS_ENERGY: "demand_gross_energy_daily",
            Metric.GENERATION_RENEWABLE: "generation_renewable_sum",
            Metric.GENERATION_RENEWABLE_ENERGY: "generation_renewable_energy_daily",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE: "generation_renewable_with_storage_sum",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY: "generation_renewable_with_storage_energy_daily",
            Metric.CURTAILMENT: "curtailment_total_daily",
            Metric.CURTAILMENT_ENERGY: "curtailment_energy_total_daily",
            Metric.CURTAILMENT_SOLAR_UTILITY: "curtailment_solar_total_daily",
            Metric.CURTAILMENT_WIND: "curtailment_wind_total_daily",
            Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY: "curtailment_energy_solar_total_daily",
            Metric.CURTAILMENT_WIND_ENERGY: "curtailment_energy_wind_total_daily",
            Metric.RENEWABLE_PROPORTION: "round(if(sum(demand_gross_sum) > 0, (sum(generation_renewable_sum) / sum(demand_gross_sum)) * 100, 0), 2)",  # noqa: E501
            Metric.RENEWABLE_WITH_STORAGE_PROPORTION: "round(if(sum(demand_gross_sum) > 0, (sum(generation_renewable_with_storage_sum) / sum(demand_gross_sum)) * 100, 0), 2)",  # noqa: E501
            Metric.FLOW_IMPORTS: "energy_imports_daily * 12",
            Metric.FLOW_EXPORTS: "energy_exports_daily * 12",
            Metric.FLOW_IMPORTS_ENERGY: "energy_imports_daily",
            Metric.FLOW_EXPORTS_ENERGY: "energy_exports_daily",
        },
        daily_metric_agg_functions={
            Metric.PRICE: "",
            Metric.DEMAND: "sum",
            Metric.DEMAND_ENERGY: "sum",
            Metric.DEMAND_GROSS: "sum",
            Metric.DEMAND_GROSS_ENERGY: "sum",
            Metric.GENERATION_RENEWABLE: "sum",
            Metric.GENERATION_RENEWABLE_ENERGY: "sum",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE: "sum",
            Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY: "sum",
            Metric.CURTAILMENT: "sum",
            Metric.CURTAILMENT_ENERGY: "sum",
            Metric.CURTAILMENT_SOLAR_UTILITY: "sum",
            Metric.CURTAILMENT_WIND: "sum",
            Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY: "sum",
            Metric.CURTAILMENT_WIND_ENERGY: "sum",
            Metric.RENEWABLE_PROPORTION: "",
            Metric.RENEWABLE_WITH_STORAGE_PROPORTION: "",
            Metric.FLOW_IMPORTS: "sum",
            Metric.FLOW_EXPORTS: "sum",
            Metric.FLOW_IMPORTS_ENERGY: "sum",
            Metric.FLOW_EXPORTS_ENERGY: "sum",
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
            DataMetric.STORAGE_BATTERY: "energy_storage",
        },
        # POWER (MW) is an instantaneous rate -> avg.  ENERGY/EMISSIONS/MARKET_VALUE are per-interval
        # quantities (MWh, tCO2, $) and remain sum.  See issue opennem#523.
        metric_agg_functions={
            DataMetric.POWER: "avg",
            DataMetric.ENERGY: "sum",
            DataMetric.EMISSIONS: "sum",
            DataMetric.MARKET_VALUE: "sum",
            DataMetric.STORAGE_BATTERY: "avg",
        },
        # Daily MV stores generated as sum(generated) per day, so an interval-weighted average is
        # required to recover average power across day/week/month/etc.
        daily_metric_columns={
            DataMetric.POWER: "round(sum(generated) / nullIf(sum(interval_count), 0), 6)",
            DataMetric.STORAGE_BATTERY: "round(sum(energy_storage_sum) / nullIf(sum(energy_storage_count), 0), 6)",
        },
        daily_metric_agg_functions={
            DataMetric.POWER: "",
            DataMetric.STORAGE_BATTERY: "",
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
            DataMetric.STORAGE_BATTERY: "energy_storage",
        },
        metric_agg_functions={
            DataMetric.POWER: "avg",
            DataMetric.ENERGY: "sum",
            DataMetric.EMISSIONS: "sum",
            DataMetric.MARKET_VALUE: "sum",
            DataMetric.STORAGE_BATTERY: "avg",
        },
        daily_metric_columns={
            DataMetric.POWER: "round(sum(generated) / nullIf(sum(interval_count), 0), 6)",
            DataMetric.STORAGE_BATTERY: "round(sum(energy_storage_sum) / nullIf(sum(energy_storage_count), 0), 6)",
        },
        daily_metric_agg_functions={
            DataMetric.POWER: "",
            DataMetric.STORAGE_BATTERY: "",
        },
    ),
}


def get_timeseries_query(
    query_type: QueryType,
    network: NetworkSchema,
    metrics: Sequence[MetricType],
    interval: Interval,
    date_start: datetime,
    date_end: datetime,
    primary_grouping: PrimaryGrouping = PrimaryGrouping.NETWORK,
    secondary_groupings: list[SecondaryGrouping] | None = None,
    # filters
    facility_code: list[str] | None = None,
    unit_code: list[str] | None = None,
    network_region: str | None = None,
    fueltech: list[str] | None = None,
    fueltech_group: list[str] | None = None,
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
        fueltech: Optional fueltechs to filter by
        fueltech_group: Optional fueltech groups to filter by

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
        date_start = date_start.date()  # type: ignore
        date_end = date_end.date()  # type: ignore

    # Pass IN-clause collections as tuples — clickhouse-driver renders lists as `IN [a, b]`
    # (CH Array literal); tuples render as `IN (a, b)` which is the conventional SQL form and
    # avoids analyzer edge cases.
    network_codes = [c for c in network.get_network_codes() if c != "OPENNEM_ROOFTOP_BACKFILL"]
    params = {
        "network": tuple(network_codes),
        "date_start": date_start,
        "date_end": date_end,
    }

    # logger.info(f"Querying {table_name} for {network.code} from {date_start} to {date_end}")

    # Build metric selection part with better error handling
    metric_selects = []
    for m in metrics:
        if m not in config.metric_columns:
            available_metrics = ", ".join(str(k.value) for k in config.metric_columns.keys())
            raise ValueError(
                f"Metric '{m.value}' not supported for {query_type.value} query. Available metrics: {available_metrics}"
            )
        if m not in config.metric_agg_functions:
            raise ValueError(f"No aggregation function defined for metric '{m.value}'")
        col = config.get_metric_column(m, table_name)
        agg = config.get_metric_agg(m, table_name)
        # Round in ClickHouse to avoid per-float Python rounding overhead. When the column
        # expression already aggregates (agg=""), emit it as-is — wrapping with an extra round()
        # around a column that already contains round() can trigger a ClickHouse analyzer bug
        # ("aggregate function found inside another aggregate") in queries that also reference
        # the same source column under a different aggregate elsewhere in the SELECT.
        if agg:
            metric_selects.append(f"round({agg}({col}), 6) as {m.value.lower()}")
        else:
            metric_selects.append(f"{col} as {m.value.lower()}")

    # Build grouping columns based on query type
    group_cols = [f"'{network.code}' as network"]
    group_cols_names = ["network"]

    if query_type == QueryType.FACILITY:
        group_cols.extend(["facility_code", "unit_code"])
        group_cols_names.extend(["facility_code", "unit_code"])
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
        params["facility_code"] = tuple(facility_code)

    if unit_code:
        where_clauses.append("unit_code in %(unit_code)s")
        params["unit_code"] = tuple(unit_code)

    if network_region:
        where_clauses.append("network_region = %(network_region)s")
        params["network_region"] = network_region

    if fueltech:
        where_clauses.append("fueltech_id in %(fueltech)s")
        params["fueltech"] = tuple(fueltech)

    if fueltech_group:
        where_clauses.append("fueltech_group_id in %(fueltech_group)s")
        params["fueltech_group"] = tuple(fueltech_group)

    # Group/order by alias names rather than positional references — the constant `'NEM' as network`
    # column makes positional GROUP BY fragile under the new ClickHouse analyzer, especially when
    # the SELECT mixes avg() and arithmetic sum() expressions (e.g. renewable_proportion).
    group_by_names = ", ".join(group_cols_names)
    query = f"""
        SELECT
            {time_fn} as interval,
            {", ".join(group_cols)},
            {", ".join(metric_selects)}
        FROM {table_name} FINAL
        WHERE {" AND ".join(where_clauses)}
        GROUP BY
            interval,
            {group_by_names}
        ORDER BY
            interval DESC,
            {group_by_names}
    """

    # Build list of column names in order
    column_names = ["interval"]
    column_names.extend(group_cols_names)
    column_names.extend(m.value.lower() for m in metrics)

    return query, params, column_names
