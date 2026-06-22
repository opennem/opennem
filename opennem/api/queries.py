"""
Unified query builder for OpenNEM API time series data.

Builds a two-stage CTE query for both market and data endpoints:

1. **Inner** SELECT pre-aggregates per raw 5-minute interval × all grouping
   dimensions, *summing across units* for per-unit source tables (unit_intervals).
   This produces one row per raw interval per group.

2. **Outer** SELECT applies the bucket function (`toStartOfHour`/`Day`/`Week`/etc.)
   and per-metric final aggregation — `avg(...)` for instantaneous MW-class
   metrics, `sum(...)` for cumulative MWh/MWh-like metrics, or a derived ratio
   expression for proportions.

Why this shape: pre-#525 the SELECT applied a single aggregation directly,
which produces incorrect results whenever the GROUP BY collapses multiple
units into a single row (e.g. network-aggregate POWER) because the
aggregation runs across the unit dimension as well as the time dimension.
The two-stage form separates "collapse the unit dimension at each raw
interval" from "collapse the time dimension into the bucket", which is the
only mathematically correct way to compute MW averages over arbitrary
grouping levels.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from opennem.api.data.schema import DataMetric
from opennem.api.market.schema import MarketMetric
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval, get_interval_function
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.api.queries")

type MetricType = DataMetric | MarketMetric | Metric


class QueryType(StrEnum):
    """Type of query to build."""

    MARKET = "market"
    DATA = "data"
    FACILITY = "facility"


@dataclass(frozen=True)
class MetricPlan:
    """How to compute a single metric in the two-stage aggregation.

    inner: alias -> SQL expression applied at the raw 5-minute level. Multiple
           metrics can share aliases — they get emitted once in the inner SELECT.
    outer: SQL expression for the outer SELECT, referring to inner aliases.
           Wrapped with the metric value as `<expr> AS <metric_name>` by the builder.
    """

    inner: dict[str, str]
    outer: str


DATA_METRIC_PLANS: dict[DataMetric, MetricPlan] = {
    DataMetric.POWER: MetricPlan(
        inner={"generated_sum": "sum(generated)"},
        outer="round(avg(generated_sum), 6)",
    ),
    DataMetric.ENERGY: MetricPlan(
        inner={"energy_sum": "sum(energy)"},
        outer="round(sum(energy_sum), 6)",
    ),
    DataMetric.EMISSIONS: MetricPlan(
        inner={"emissions_sum": "sum(emissions)"},
        outer="round(sum(emissions_sum), 6)",
    ),
    DataMetric.MARKET_VALUE: MetricPlan(
        inner={"market_value_sum": "sum(market_value)"},
        outer="round(sum(market_value_sum), 6)",
    ),
    DataMetric.STORAGE_BATTERY: MetricPlan(
        # State of charge: sum non-null values and count of contributing intervals.
        # Outer weighted-average yields the avg SoC over the bucket × unit set.
        inner={
            "energy_storage_sum": "sum(coalesce(energy_storage, 0))",
            "energy_storage_count": "countIf(energy_storage IS NOT NULL)",
        },
        outer="round(sum(energy_storage_sum) / nullIf(sum(energy_storage_count), 0), 6)",
    ),
}

# Market metrics live on `market_summary` which is already per (interval, region).
# Inner sums across region rows when the query is network-aggregate; selects single rows
# when filtered to one region. Outer aggregates across raw intervals to the bucket.
MARKET_METRIC_PLANS: dict[Metric, MetricPlan] = {
    Metric.PRICE: MetricPlan(
        inner={
            "price_sum_inner": "sum(price)",
            "price_count_inner": "countIf(price IS NOT NULL)",
        },
        outer="round(sum(price_sum_inner) / nullIf(sum(price_count_inner), 0), 6)",
    ),
    Metric.DEMAND: MetricPlan(
        inner={"demand_sum_inner": "sum(demand)"},
        outer="round(avg(demand_sum_inner), 6)",
    ),
    Metric.DEMAND_ENERGY: MetricPlan(
        inner={"demand_energy_sum": "sum(demand_energy)"},
        outer="round(sum(demand_energy_sum), 6)",
    ),
    Metric.DEMAND_GROSS: MetricPlan(
        inner={"demand_gross_sum_inner": "sum(demand_gross)"},
        outer="round(avg(demand_gross_sum_inner), 6)",
    ),
    Metric.DEMAND_GROSS_ENERGY: MetricPlan(
        inner={"demand_gross_energy_sum": "sum(demand_gross_energy)"},
        outer="round(sum(demand_gross_energy_sum), 6)",
    ),
    Metric.GENERATION_RENEWABLE: MetricPlan(
        inner={"gr_sum_inner": "sum(generation_renewable)"},
        outer="round(avg(gr_sum_inner), 6)",
    ),
    Metric.GENERATION_RENEWABLE_ENERGY: MetricPlan(
        inner={"gr_energy_sum": "sum(generation_renewable_energy)"},
        outer="round(sum(gr_energy_sum), 6)",
    ),
    Metric.GENERATION_RENEWABLE_WITH_STORAGE: MetricPlan(
        inner={"grws_sum_inner": "sum(generation_renewable_with_storage)"},
        outer="round(avg(grws_sum_inner), 6)",
    ),
    Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY: MetricPlan(
        inner={"grws_energy_sum": "sum(generation_renewable_with_storage_energy)"},
        outer="round(sum(grws_energy_sum), 6)",
    ),
    Metric.CURTAILMENT: MetricPlan(
        inner={"curtailment_total_inner": "sum(curtailment_total)"},
        outer="round(avg(curtailment_total_inner), 6)",
    ),
    Metric.CURTAILMENT_ENERGY: MetricPlan(
        inner={"curtailment_energy_total_sum": "sum(curtailment_energy_total)"},
        outer="round(sum(curtailment_energy_total_sum), 6)",
    ),
    Metric.CURTAILMENT_SOLAR_UTILITY: MetricPlan(
        inner={"curtailment_solar_total_inner": "sum(curtailment_solar_total)"},
        outer="round(avg(curtailment_solar_total_inner), 6)",
    ),
    Metric.CURTAILMENT_WIND: MetricPlan(
        inner={"curtailment_wind_total_inner": "sum(curtailment_wind_total)"},
        outer="round(avg(curtailment_wind_total_inner), 6)",
    ),
    Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY: MetricPlan(
        inner={"curtailment_energy_solar_total_sum": "sum(curtailment_energy_solar_total)"},
        outer="round(sum(curtailment_energy_solar_total_sum), 6)",
    ),
    Metric.CURTAILMENT_WIND_ENERGY: MetricPlan(
        inner={"curtailment_energy_wind_total_sum": "sum(curtailment_energy_wind_total)"},
        outer="round(sum(curtailment_energy_wind_total_sum), 6)",
    ),
    # Flows: source col is MWh per 5min. MW = MWh × 12 (intervals per hour). Sum-across-regions
    # at the inner level, then `avg(MW_per_interval)` outside for the MW metric, or `sum(MWh_per_interval)`
    # for the energy metric.
    Metric.FLOW_IMPORTS: MetricPlan(
        inner={"energy_imports_sum_inner": "sum(energy_imports)"},
        outer="round(avg(energy_imports_sum_inner * 12), 6)",
    ),
    Metric.FLOW_EXPORTS: MetricPlan(
        inner={"energy_exports_sum_inner": "sum(energy_exports)"},
        outer="round(avg(energy_exports_sum_inner * 12), 6)",
    ),
    Metric.FLOW_IMPORTS_ENERGY: MetricPlan(
        inner={"energy_imports_sum_inner": "sum(energy_imports)"},
        outer="round(sum(energy_imports_sum_inner), 6)",
    ),
    Metric.FLOW_EXPORTS_ENERGY: MetricPlan(
        inner={"energy_exports_sum_inner": "sum(energy_exports)"},
        outer="round(sum(energy_exports_sum_inner), 6)",
    ),
    # Proportions: sum the underlying components across the bucket, then divide.
    # NULL (not 0) when demand_gross is absent for the bucket. The freshest/settling
    # interval can be served before demand_gross lands (generation_renewable and
    # demand_gross arrive on different paths), and a literal-0 fallback produced a
    # spurious 0% that "healed" on the next poll (#575). NULL serialises to `null`,
    # signalling "not yet available" rather than a non-physical 0%.
    Metric.RENEWABLE_PROPORTION: MetricPlan(
        inner={"gr_sum_inner": "sum(generation_renewable)", "dg_sum_inner": "sum(demand_gross)"},
        outer="if(sum(dg_sum_inner) > 0, round((sum(gr_sum_inner) / sum(dg_sum_inner)) * 100, 2), NULL)",
    ),
    Metric.RENEWABLE_WITH_STORAGE_PROPORTION: MetricPlan(
        inner={"grws_sum_inner": "sum(generation_renewable_with_storage)", "dg_sum_inner": "sum(demand_gross)"},
        outer="if(sum(dg_sum_inner) > 0, round((sum(grws_sum_inner) / sum(dg_sum_inner)) * 100, 2), NULL)",
    ),
}


@dataclass(frozen=True)
class QueryConfig:
    """Configuration for building a time series query."""

    query_type: QueryType
    base_table: str
    plans: dict[MetricType, MetricPlan]


QUERY_CONFIGS: dict[QueryType, QueryConfig] = {
    QueryType.MARKET: QueryConfig(QueryType.MARKET, "market_summary", MARKET_METRIC_PLANS),  # type: ignore[arg-type]
    QueryType.DATA: QueryConfig(QueryType.DATA, "unit_intervals", DATA_METRIC_PLANS),  # type: ignore[arg-type]
    QueryType.FACILITY: QueryConfig(QueryType.FACILITY, "unit_intervals", DATA_METRIC_PLANS),  # type: ignore[arg-type]
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
    """Build a CTE-based time-series query for the given parameters.

    See module docstring for the structural design.
    """
    config = QUERY_CONFIGS[query_type]

    # ---- collect required inner columns (dedup by alias) ----
    inner_aliases: dict[str, str] = {}
    for m in metrics:
        if m not in config.plans:
            available = ", ".join(str(k.value) for k in config.plans)
            raise ValueError(f"Metric '{m.value}' not supported for {query_type.value} query. Available: {available}")
        for alias, expr in config.plans[m].inner.items():
            inner_aliases.setdefault(alias, expr)

    # ---- decide grouping columns ----
    # NetworkSchema.get_network_codes() can return multiple network_id values for one logical
    # network (e.g. NEM expands to ['NEM', 'AEMO_ROOFTOP']). We treat them as a single network
    # for output purposes — that's why network_id is NOT in the grouping list. The WHERE clause
    # constrains them, and inner sum-across-units collapses them into one per-interval value.
    inner_extra_groups: list[str] = []
    outer_extra_groups: list[str] = []

    is_unit_table = config.base_table == "unit_intervals"

    if query_type == QueryType.FACILITY and is_unit_table:
        # FACILITY exposes per-unit rows.
        inner_extra_groups.extend(["facility_code", "unit_code"])
        outer_extra_groups.extend(["facility_code", "unit_code"])

    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        inner_extra_groups.append("network_region")
        outer_extra_groups.append("network_region")

    # Secondary groupings (DATA only — never combined with FACILITY).
    secondary_select_aliases: list[str] = []
    if query_type == QueryType.DATA and secondary_groupings:
        for sg in secondary_groupings:
            if sg == SecondaryGrouping.RENEWABLE:
                inner_extra_groups.append("renewable")
                outer_extra_groups.append("renewable")
            elif sg == SecondaryGrouping.FUELTECH:
                inner_extra_groups.append("fueltech_id")
                outer_extra_groups.append("fueltech_id")
                secondary_select_aliases.append("fueltech_id AS fueltech")
            elif sg == SecondaryGrouping.FUELTECH_GROUP:
                inner_extra_groups.append("fueltech_group_id")
                outer_extra_groups.append("fueltech_group_id")
                secondary_select_aliases.append("fueltech_group_id AS fueltech_group")
            elif sg == SecondaryGrouping.STATUS:
                inner_extra_groups.append("status_id")
                outer_extra_groups.append("status_id")
                secondary_select_aliases.append("status_id AS status")

    # Time column on the base table is `interval` for both unit_intervals and market_summary.
    time_col = "interval"

    # ---- params ----
    network_codes = network.get_network_codes()
    params: dict = {
        "network": tuple(network_codes),
        "date_start": date_start.replace(tzinfo=None) if isinstance(date_start, datetime) else date_start,
        "date_end": date_end.replace(tzinfo=None) if isinstance(date_end, datetime) else date_end,
    }

    where_inner: list[str] = [
        "network_id in %(network)s",
        f"{time_col} >= %(date_start)s",
        f"{time_col} < %(date_end)s",
    ]
    if facility_code:
        where_inner.append("facility_code in %(facility_code)s")
        params["facility_code"] = tuple(facility_code)
    if unit_code:
        where_inner.append("unit_code in %(unit_code)s")
        params["unit_code"] = tuple(unit_code)
    if network_region:
        where_inner.append("network_region = %(network_region)s")
        params["network_region"] = network_region
    if fueltech:
        where_inner.append("fueltech_id in %(fueltech)s")
        params["fueltech"] = tuple(fueltech)
    if fueltech_group:
        where_inner.append("fueltech_group_id in %(fueltech_group)s")
        params["fueltech_group"] = tuple(fueltech_group)

    # ---- SQL assembly ----
    inner_select_lines = [
        f"{time_col} AS raw_interval",
        *inner_extra_groups,
        *(f"{expr} AS {alias}" for alias, expr in inner_aliases.items()),
    ]
    inner_group_by = ["raw_interval", *inner_extra_groups]

    bucket_fn = get_interval_function(interval, "raw_interval", database="clickhouse")

    outer_select_metrics = [f"{config.plans[m].outer} AS {m.value.lower()}" for m in metrics]
    # Emit `network` as a constant literal — it's not a true GROUP BY dimension.
    outer_select_groups = [f"'{network.code}' AS network", *outer_extra_groups]
    # Rename fueltech_id/fueltech_group_id with their output alias names.
    aliased_outer_groups: list[str] = []
    for col in outer_extra_groups:
        if col == "fueltech_id":
            aliased_outer_groups.append("fueltech_id AS fueltech")
        elif col == "fueltech_group_id":
            aliased_outer_groups.append("fueltech_group_id AS fueltech_group")
        elif col == "status_id":
            aliased_outer_groups.append("status_id AS status")
        else:
            aliased_outer_groups.append(col)
    outer_select_groups = [f"'{network.code}' AS network", *aliased_outer_groups]

    outer_group_by = ["interval", *outer_extra_groups] if outer_extra_groups else ["interval"]
    order_by_extra = [", " + ", ".join(outer_extra_groups)] if outer_extra_groups else [""]

    sql = f"""
    WITH inner_agg AS (
        SELECT
            {", ".join(inner_select_lines)}
        FROM {config.base_table} FINAL
        WHERE {" AND ".join(where_inner)}
        GROUP BY {", ".join(inner_group_by)}
    )
    SELECT
        {bucket_fn} AS interval,
        {", ".join(outer_select_groups)},
        {", ".join(outer_select_metrics)}
    FROM inner_agg
    GROUP BY {", ".join(outer_group_by)}
    ORDER BY interval DESC{order_by_extra[0]}
    """

    # ---- column-name order (used by callers to zip with row tuples) ----
    column_names: list[str] = ["interval", "network"]
    if query_type == QueryType.FACILITY:
        column_names.extend(["facility_code", "unit_code"])
    if primary_grouping == PrimaryGrouping.NETWORK_REGION:
        column_names.append("network_region")
    if query_type == QueryType.DATA and secondary_groupings:
        for sg in secondary_groupings:
            if sg == SecondaryGrouping.RENEWABLE:
                column_names.append("renewable")
            elif sg == SecondaryGrouping.FUELTECH:
                column_names.append("fueltech")
            elif sg == SecondaryGrouping.FUELTECH_GROUP:
                column_names.append("fueltech_group")
            elif sg == SecondaryGrouping.STATUS:
                column_names.append("status")
    column_names.extend(m.value.lower() for m in metrics)

    return sql, params, column_names
