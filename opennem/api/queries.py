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

Source table by bucket size: sub-daily buckets (5m, 1h) read the raw tables
(`unit_intervals` / `market_summary`); day-or-coarser buckets read the daily
materialised views, whose rows already hold each day's sums and distinct raw
interval count — see the "Daily materialised-view plans" section. A 4-year
monthly fuel-tech query drops from ~70s to under 100ms on the views.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
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
    edge:  daily-view plans only — alias -> expression over the *raw* table that
           yields the same aliases as `inner`, used for the partial days at either
           end of a request that the day-keyed views cannot serve.
    """

    inner: dict[str, str]
    outer: str
    edge: dict[str, str] | None = None


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


# ---------------------------------------------------------------------------
# Daily materialised-view plans
#
# For buckets of a day or coarser the inner stage reads the pre-aggregated daily
# views (opennem/db/clickhouse/views.py) for every whole day in the request, and the
# raw 5-minute table for the partial day (if any) at either end — a request that
# starts or ends mid-day, or a live request capped at the last settled interval.
# Whole days come out of the view keyed per day; edge intervals come out of the raw
# table keyed per raw interval; both feed the same outer bucket aggregation, so:
#
#   * cumulative metrics (MWh, tCO2, $) — sum the daily/interval sums; identical to raw.
#   * instantaneous metrics (MW) — raw is `avg(per-interval sum)` over the bucket, i.e.
#     `sum(x) / n_intervals_where_x_has_a_value`. Daily rows carry a `<x>_slots` bitmap
#     of the 5-minute slots where x was non-NULL; the inner stage merges the bitmaps of
#     every key the query collapses (regions / fuel techs / units / a 30-min rooftop key
#     beside 5-min keys) per day, giving the exact distinct-interval count; edge rows
#     emit 1 when the interval has a value; the outer divides the bucket sum by the sum
#     of those counts. Identical to raw, NULL gaps and complementary key gaps included.
#   * ratios — sum both components across the bucket, then divide; identical to raw.
#
# STATUS grouping stays on the raw table: the unit view stores one status per unit-day.

DAILY_INTERVALS: frozenset[Interval] = frozenset(
    {
        Interval.DAY,
        Interval.WEEK,
        Interval.MONTH,
        Interval.QUARTER,
        Interval.SEASON,
        Interval.YEAR,
        Interval.FINANCIAL_YEAR,
    }
)


def _daily_mw(alias: str, daily_col: str, raw_col: str, scale: str = "") -> MetricPlan:
    """MW-class metric: bucket sum / count of raw intervals carrying a value.

    The daily views store a `<raw_col>_slots` bitmap of 5-minute slots where the
    source column was non-NULL; merging it across the keys a query collapses gives
    the exact distinct-interval count the raw path's `avg()` implicitly uses.
    """
    n = f"{alias}_n"
    return MetricPlan(
        inner={alias: f"sum({daily_col})", n: f"groupBitmapMerge({raw_col}_slots)"},
        edge={alias: f"sum({raw_col})", n: f"if(sum({raw_col}) IS NOT NULL, 1, 0)"},
        outer=f"round(sum({alias}){scale} / nullIf(sum({n}), 0), 6)",
    )


def _daily_sum(alias: str, daily_col: str, raw_col: str) -> MetricPlan:
    """Cumulative metric: plain bucket sum."""
    return MetricPlan(
        inner={alias: f"sum({daily_col})"},
        edge={alias: f"sum({raw_col})"},
        outer=f"round(sum({alias}), 6)",
    )


DATA_METRIC_PLANS_DAILY: dict[DataMetric, MetricPlan] = {
    DataMetric.POWER: _daily_mw("generated_sum", "generated", "generated"),
    DataMetric.ENERGY: _daily_sum("energy_sum", "energy", "energy"),
    DataMetric.EMISSIONS: _daily_sum("emissions_sum", "emissions", "emissions"),
    DataMetric.MARKET_VALUE: _daily_sum("market_value_sum", "market_value", "market_value"),
    DataMetric.STORAGE_BATTERY: MetricPlan(
        inner={
            "energy_storage_sum": "sum(energy_storage_sum)",
            "energy_storage_count": "sum(energy_storage_count)",
        },
        edge={
            "energy_storage_sum": "sum(coalesce(energy_storage, 0))",
            "energy_storage_count": "countIf(energy_storage IS NOT NULL)",
        },
        outer="round(sum(energy_storage_sum) / nullIf(sum(energy_storage_count), 0), 6)",
    ),
}


def _ratio_plan(numerator_alias: str, numerator_daily: str, numerator_raw: str) -> MetricPlan:
    return MetricPlan(
        inner={numerator_alias: f"sum({numerator_daily})", "dg_sum_inner": "sum(demand_gross_sum)"},
        edge={numerator_alias: f"sum({numerator_raw})", "dg_sum_inner": "sum(demand_gross)"},
        outer=f"if(sum(dg_sum_inner) > 0, round((sum({numerator_alias}) / sum(dg_sum_inner)) * 100, 2), NULL)",
    )


MARKET_METRIC_PLANS_DAILY: dict[Metric, MetricPlan] = {
    Metric.PRICE: MetricPlan(
        inner={"price_sum_inner": "sum(price_sum)", "price_count_inner": "sum(price_count)"},
        edge={"price_sum_inner": "sum(price)", "price_count_inner": "countIf(price IS NOT NULL)"},
        outer="round(sum(price_sum_inner) / nullIf(sum(price_count_inner), 0), 6)",
    ),
    Metric.DEMAND: _daily_mw("demand_sum_inner", "demand_sum", "demand"),
    Metric.DEMAND_ENERGY: _daily_sum("demand_energy_sum", "demand_energy_daily", "demand_energy"),
    Metric.DEMAND_GROSS: _daily_mw("demand_gross_sum_inner", "demand_gross_sum", "demand_gross"),
    Metric.DEMAND_GROSS_ENERGY: _daily_sum("demand_gross_energy_sum", "demand_gross_energy_daily", "demand_gross_energy"),
    Metric.GENERATION_RENEWABLE: _daily_mw("gr_sum_inner", "generation_renewable_sum", "generation_renewable"),
    Metric.GENERATION_RENEWABLE_ENERGY: _daily_sum(
        "gr_energy_sum", "generation_renewable_energy_daily", "generation_renewable_energy"
    ),
    Metric.GENERATION_RENEWABLE_WITH_STORAGE: _daily_mw(
        "grws_sum_inner", "generation_renewable_with_storage_sum", "generation_renewable_with_storage"
    ),
    Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY: _daily_sum(
        "grws_energy_sum", "generation_renewable_with_storage_energy_daily", "generation_renewable_with_storage_energy"
    ),
    Metric.CURTAILMENT: _daily_mw("curtailment_total_inner", "curtailment_total_daily", "curtailment_total"),
    Metric.CURTAILMENT_ENERGY: _daily_sum(
        "curtailment_energy_total_sum", "curtailment_energy_total_daily", "curtailment_energy_total"
    ),
    Metric.CURTAILMENT_SOLAR_UTILITY: _daily_mw(
        "curtailment_solar_total_inner", "curtailment_solar_total_daily", "curtailment_solar_total"
    ),
    Metric.CURTAILMENT_WIND: _daily_mw("curtailment_wind_total_inner", "curtailment_wind_total_daily", "curtailment_wind_total"),
    Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY: _daily_sum(
        "curtailment_energy_solar_total_sum", "curtailment_energy_solar_total_daily", "curtailment_energy_solar_total"
    ),
    Metric.CURTAILMENT_WIND_ENERGY: _daily_sum(
        "curtailment_energy_wind_total_sum", "curtailment_energy_wind_total_daily", "curtailment_energy_wind_total"
    ),
    # Flows: source is MWh per 5-min interval; MW = MWh × 12.
    Metric.FLOW_IMPORTS: _daily_mw("energy_imports_sum_inner", "energy_imports_daily", "energy_imports", scale=" * 12"),
    Metric.FLOW_EXPORTS: _daily_mw("energy_exports_sum_inner", "energy_exports_daily", "energy_exports", scale=" * 12"),
    Metric.FLOW_IMPORTS_ENERGY: _daily_sum("energy_imports_sum_inner", "energy_imports_daily", "energy_imports"),
    Metric.FLOW_EXPORTS_ENERGY: _daily_sum("energy_exports_sum_inner", "energy_exports_daily", "energy_exports"),
    Metric.RENEWABLE_PROPORTION: _ratio_plan("gr_sum_inner", "generation_renewable_sum", "generation_renewable"),
    Metric.RENEWABLE_WITH_STORAGE_PROPORTION: _ratio_plan(
        "grws_sum_inner", "generation_renewable_with_storage_sum", "generation_renewable_with_storage"
    ),
}


@dataclass(frozen=True)
class QueryConfig:
    """Configuration for building a time series query.

    `base_table`/`plans` serve sub-daily buckets from the raw interval tables;
    `daily_table`/`daily_plans` serve day-or-coarser buckets from the daily views.
    `unit_daily_table` is the per-unit daily view, used when the query needs unit-level
    dimensions (facility/unit codes, renewable flag, status) the fueltech view lacks.
    """

    query_type: QueryType
    base_table: str
    plans: dict[MetricType, MetricPlan]
    daily_table: str
    daily_plans: dict[MetricType, MetricPlan]
    unit_daily_table: str | None = None


QUERY_CONFIGS: dict[QueryType, QueryConfig] = {
    QueryType.MARKET: QueryConfig(
        QueryType.MARKET,
        "market_summary",
        MARKET_METRIC_PLANS,  # type: ignore[arg-type]
        "market_summary_daily_mv",
        MARKET_METRIC_PLANS_DAILY,  # type: ignore[arg-type]
    ),
    QueryType.DATA: QueryConfig(
        QueryType.DATA,
        "unit_intervals",
        DATA_METRIC_PLANS,  # type: ignore[arg-type]
        "fueltech_intervals_daily_mv",
        DATA_METRIC_PLANS_DAILY,  # type: ignore[arg-type]
        unit_daily_table="unit_intervals_daily_mv",
    ),
    QueryType.FACILITY: QueryConfig(
        QueryType.FACILITY,
        "unit_intervals",
        DATA_METRIC_PLANS,  # type: ignore[arg-type]
        "unit_intervals_daily_mv",
        DATA_METRIC_PLANS_DAILY,  # type: ignore[arg-type]
    ),
}


@dataclass(frozen=True)
class DailySplit:
    """How a [date_start, date_end) request maps onto whole days plus raw edges.

    `day_start`/`day_end` bound the half-open run of whole days served by the view.
    `edges` are the half-open raw-interval ranges (at most one leading, one trailing)
    the view cannot serve — empty when both bounds fall on midnight.
    """

    day_start: date
    day_end: date
    edges: tuple[tuple[datetime, datetime], ...]


def _daily_split(date_start: datetime, date_end: datetime) -> DailySplit | None:
    """Split a request into whole days plus partial edge days; None if no whole day fits."""
    day_start = date_start.date() if date_start.time() == time.min else date_start.date() + timedelta(days=1)
    day_end = date_end.date()
    if day_start >= day_end:
        return None
    edges: list[tuple[datetime, datetime]] = []
    if date_start.time() != time.min:
        edges.append((date_start, datetime.combine(day_start, time.min)))
    if date_end.time() != time.min:
        edges.append((datetime.combine(day_end, time.min), date_end))
    return DailySplit(day_start, day_end, tuple(edges))


def _daily_table_for(
    config: QueryConfig,
    query_type: QueryType,
    secondary_groupings: list[SecondaryGrouping] | None,
    facility_code: list[str] | None,
    unit_code: list[str] | None,
) -> str:
    """Pick the per-unit daily view when unit-level dimensions or filters are needed."""
    needs_unit_dims = query_type == QueryType.FACILITY or bool(facility_code) or bool(unit_code)
    if secondary_groupings:
        needs_unit_dims |= SecondaryGrouping.RENEWABLE in secondary_groupings
    if needs_unit_dims and config.unit_daily_table:
        return config.unit_daily_table
    return config.daily_table


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

    # Day-or-coarser buckets read the daily views for whole days plus the raw table for
    # partial edge days. Sub-daily buckets, STATUS grouping, and requests too short to
    # contain a whole day read the raw table only.
    split = _daily_split(date_start, date_end) if interval in DAILY_INTERVALS else None
    if secondary_groupings and SecondaryGrouping.STATUS in secondary_groupings:
        split = None
    use_daily = split is not None
    plans = config.daily_plans if use_daily else config.plans
    base_table = (
        _daily_table_for(config, query_type, secondary_groupings, facility_code, unit_code) if use_daily else config.base_table
    )

    # ---- collect required inner columns (dedup by alias) ----
    inner_aliases: dict[str, str] = {}
    edge_aliases: dict[str, str] = {}
    for m in metrics:
        if m not in plans:
            available = ", ".join(str(k.value) for k in plans)
            raise ValueError(f"Metric '{m.value}' not supported for {query_type.value} query. Available: {available}")
        for alias, expr in plans[m].inner.items():
            inner_aliases.setdefault(alias, expr)
        if use_daily:
            for alias, expr in (plans[m].edge or {}).items():
                edge_aliases.setdefault(alias, expr)

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

    # ---- params ----
    network_codes = network.get_network_codes()
    params: dict = {"network": tuple(network_codes)}

    filters: list[str] = ["network_id in %(network)s"]
    if facility_code:
        filters.append("facility_code in %(facility_code)s")
        params["facility_code"] = tuple(facility_code)
    if unit_code:
        filters.append("unit_code in %(unit_code)s")
        params["unit_code"] = tuple(unit_code)
    if network_region:
        filters.append("network_region = %(network_region)s")
        params["network_region"] = network_region
    if fueltech:
        filters.append("fueltech_id in %(fueltech)s")
        params["fueltech"] = tuple(fueltech)
    if fueltech_group:
        filters.append("fueltech_group_id in %(fueltech_group)s")
        params["fueltech_group"] = tuple(fueltech_group)

    # Raw tables key on `interval` (DateTime64); daily views key on `date` (Date).
    where_edge: list[str] | None = None
    if split is not None:
        params["day_start"], params["day_end"] = split.day_start, split.day_end
        where_inner = [*filters, "date >= %(day_start)s", "date < %(day_end)s"]
        edge_ranges: list[str] = []
        for i, (edge_start, edge_end) in enumerate(split.edges):
            params[f"edge{i}_start"] = edge_start.replace(tzinfo=None)
            params[f"edge{i}_end"] = edge_end.replace(tzinfo=None)
            edge_ranges.append(f"(interval >= %(edge{i}_start)s AND interval < %(edge{i}_end)s)")
        if edge_ranges:
            where_edge = [*filters, "(" + " OR ".join(edge_ranges) + ")"]
    else:
        params["date_start"] = date_start.replace(tzinfo=None) if isinstance(date_start, datetime) else date_start
        params["date_end"] = date_end.replace(tzinfo=None) if isinstance(date_end, datetime) else date_end
        where_inner = [*filters, "interval >= %(date_start)s", "interval < %(date_end)s"]

    # ---- SQL assembly ----
    inner_select_lines = [
        "toDateTime64(date, 3) AS raw_interval" if use_daily else "interval AS raw_interval",
        *inner_extra_groups,
        *(f"{expr} AS {alias}" for alias, expr in inner_aliases.items()),
    ]
    inner_group_by = ["raw_interval", *inner_extra_groups]

    # Partial edge days come from the raw table with the same alias set, unioned in
    # before bucketing so the outer aggregation treats both sources alike.
    edge_sql = ""
    if where_edge is not None:
        missing = [alias for alias in inner_aliases if alias not in edge_aliases]
        if missing:
            raise ValueError(f"Daily plan lacks edge expressions for: {missing}")
        edge_select_lines = [
            "interval AS raw_interval",
            *inner_extra_groups,
            *(f"{edge_aliases[alias]} AS {alias}" for alias in inner_aliases),
        ]
        edge_sql = f"""
        UNION ALL
        SELECT
            {", ".join(edge_select_lines)}
        FROM {config.base_table} FINAL
        WHERE {" AND ".join(where_edge)}
        GROUP BY {", ".join(inner_group_by)}"""

    bucket_fn = get_interval_function(interval, "raw_interval", database="clickhouse")

    outer_select_metrics = [f"{plans[m].outer} AS {m.value.lower()}" for m in metrics]
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
        FROM {base_table} FINAL
        WHERE {" AND ".join(where_inner)}
        GROUP BY {", ".join(inner_group_by)}{edge_sql}
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
