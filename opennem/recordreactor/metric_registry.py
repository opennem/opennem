"""
Declarative metric configuration for milestone record detection.

Replaces scattered conditionals in backlog.py with a single registry that defines
every valid (metric, period, grouping) combination, their source tables, column mappings,
aggregation functions, and value constraints.
"""

from dataclasses import dataclass, field
from datetime import datetime

from opennem.recordreactor.schema import MilestoneFueltechGrouping, MilestonePeriod, MilestoneType

# Source table constants
TABLE_FUELTECH_INTERVALS = "fueltech_intervals_mv"
TABLE_RENEWABLE_INTERVALS = "renewable_intervals_mv"
TABLE_MARKET_SUMMARY = "market_summary"


@dataclass
class GroupingConfig:
    """Configuration for how to group records"""

    name: str
    group_by_fields: list[str] = field(default_factory=list)


# Define all grouping configurations
GROUPING_NETWORK = GroupingConfig(name="network")
GROUPING_REGION = GroupingConfig(name="region", group_by_fields=["network_region"])
GROUPING_FUELTECH = GroupingConfig(name="fueltech", group_by_fields=["fueltech_group_id"])
GROUPING_RENEWABLE = GroupingConfig(name="renewable", group_by_fields=["renewable"])
GROUPING_REGION_FUELTECH = GroupingConfig(name="region_fueltech", group_by_fields=["network_region", "fueltech_group_id"])
GROUPING_REGION_RENEWABLE = GroupingConfig(name="region_renewable", group_by_fields=["network_region", "renewable"])

# Groupings for generation metrics (power/energy/emissions)
GENERATION_GROUPINGS = [
    GROUPING_NETWORK,
    GROUPING_REGION,
    GROUPING_FUELTECH,
    GROUPING_RENEWABLE,
    GROUPING_REGION_FUELTECH,
    GROUPING_REGION_RENEWABLE,
]

# Groupings for market metrics (price/demand/proportion) — no fueltech breakdown
MARKET_GROUPINGS = [
    GROUPING_NETWORK,
    GROUPING_REGION,
]


@dataclass
class MetricDefinition:
    """Defines how to query and detect records for a specific metric type"""

    metric: MilestoneType
    periods: list[MilestonePeriod]
    groupings: list[GroupingConfig]
    source_table: str
    time_col: str
    value_column: str
    agg_function: str  # "SUM", "AVG", or "" (for computed expressions like proportion)
    min_value: float  # floor to filter noise
    allow_negative: bool = False
    round_to: int = 0
    date_cutoff: datetime | None = None
    # fueltech-specific date cutoffs (skip records before these dates)
    fueltech_date_cutoffs: dict[str, datetime] = field(default_factory=dict)
    # minimum interval count for LOW records to be valid (by period)
    interval_thresholds: dict[MilestonePeriod, int] = field(default_factory=dict)


# Default interval thresholds for LOW record validity
_DEFAULT_INTERVAL_THRESHOLDS: dict[MilestonePeriod, int] = {
    MilestonePeriod.interval: 1,
    MilestonePeriod.day: 288,
    MilestonePeriod.week: 2016,
    MilestonePeriod.week_rolling: 2016,
    MilestonePeriod.month: 8000,
    MilestonePeriod.quarter: 24000,
    MilestonePeriod.year: 98000,
    MilestonePeriod.financial_year: 98000,
}

# Fueltech-specific date cutoffs
_FUELTECH_DATE_CUTOFFS: dict[str, datetime] = {
    MilestoneFueltechGrouping.solar.value: datetime.fromisoformat("2015-10-26T00:00:00"),
    MilestoneFueltechGrouping.wind.value: datetime.fromisoformat("2009-07-01T00:00:00"),
    MilestoneFueltechGrouping.renewables.value: datetime.fromisoformat("2000-01-01T00:00:00"),
}


def _get_source_table_for_grouping(grouping: GroupingConfig) -> str:
    """Determine the ClickHouse source table based on grouping type"""
    if "renewable" in grouping.group_by_fields:
        return TABLE_RENEWABLE_INTERVALS
    return TABLE_FUELTECH_INTERVALS


# Registry of all metric definitions
_METRIC_REGISTRY: list[MetricDefinition] = [
    # Power — only at interval level
    MetricDefinition(
        metric=MilestoneType.power,
        periods=[MilestonePeriod.interval],
        groupings=GENERATION_GROUPINGS,
        source_table=TABLE_FUELTECH_INTERVALS,  # overridden per grouping
        time_col="interval",
        value_column="generated",
        agg_function="SUM",
        min_value=100,
        fueltech_date_cutoffs=_FUELTECH_DATE_CUTOFFS,
        interval_thresholds=_DEFAULT_INTERVAL_THRESHOLDS,
    ),
    # Energy — day and above
    MetricDefinition(
        metric=MilestoneType.energy,
        periods=[MilestonePeriod.day, MilestonePeriod.month, MilestonePeriod.quarter, MilestonePeriod.year],
        groupings=GENERATION_GROUPINGS,
        source_table=TABLE_FUELTECH_INTERVALS,
        time_col="interval",
        value_column="energy",
        agg_function="SUM",
        min_value=1000,
        fueltech_date_cutoffs=_FUELTECH_DATE_CUTOFFS,
        interval_thresholds=_DEFAULT_INTERVAL_THRESHOLDS,
    ),
    # Emissions — day and above
    MetricDefinition(
        metric=MilestoneType.emissions,
        periods=[MilestonePeriod.day, MilestonePeriod.month, MilestonePeriod.quarter, MilestonePeriod.year],
        groupings=GENERATION_GROUPINGS,
        source_table=TABLE_FUELTECH_INTERVALS,
        time_col="interval",
        value_column="emissions",
        agg_function="SUM",
        min_value=1000,
        fueltech_date_cutoffs=_FUELTECH_DATE_CUTOFFS,
        interval_thresholds=_DEFAULT_INTERVAL_THRESHOLDS,
    ),
    # Price — interval only
    MetricDefinition(
        metric=MilestoneType.price,
        periods=[MilestonePeriod.interval],
        groupings=MARKET_GROUPINGS,
        source_table=TABLE_MARKET_SUMMARY,
        time_col="interval",
        value_column="price",
        agg_function="AVG",
        min_value=0,
        allow_negative=True,
        date_cutoff=datetime.fromisoformat("2009-07-01T00:00:00"),
        interval_thresholds={MilestonePeriod.interval: 1},
    ),
    # Demand — all periods
    MetricDefinition(
        metric=MilestoneType.demand,
        periods=[
            MilestonePeriod.interval,
            MilestonePeriod.day,
            MilestonePeriod.month,
            MilestonePeriod.quarter,
            MilestonePeriod.year,
        ],
        groupings=MARKET_GROUPINGS,
        source_table=TABLE_MARKET_SUMMARY,
        time_col="interval",
        value_column="demand",  # at interval level; demand_energy at day+
        agg_function="AVG",  # at interval level; SUM at day+
        min_value=100,
        date_cutoff=datetime.fromisoformat("2009-07-01T00:00:00"),
        interval_thresholds=_DEFAULT_INTERVAL_THRESHOLDS,
    ),
    # Proportion (renewable %) — all periods
    MetricDefinition(
        metric=MilestoneType.proportion,
        periods=[
            MilestonePeriod.interval,
            MilestonePeriod.day,
            MilestonePeriod.month,
            MilestonePeriod.quarter,
            MilestonePeriod.year,
        ],
        groupings=MARKET_GROUPINGS,
        source_table=TABLE_MARKET_SUMMARY,
        time_col="interval",
        value_column="round(if(sum(demand_gross) > 0, (sum(generation_renewable) / sum(demand_gross)) * 100, 0), 2)",
        agg_function="",  # pre-computed expression
        min_value=0,
        round_to=2,
        interval_thresholds=_DEFAULT_INTERVAL_THRESHOLDS,
    ),
]


def get_metric_registry() -> list[MetricDefinition]:
    """Get the full metric registry"""
    return _METRIC_REGISTRY


def get_metric_definitions_for_period(period: MilestonePeriod) -> list[MetricDefinition]:
    """Get metric definitions valid for a specific period"""
    return [m for m in _METRIC_REGISTRY if period in m.periods]


def get_source_table_for_metric_grouping(metric_def: MetricDefinition, grouping: GroupingConfig) -> str:
    """Get the correct source table for a metric + grouping combination.

    Generation metrics use different tables based on grouping:
    - renewable grouping -> renewable_intervals_mv
    - fueltech/network/region grouping -> fueltech_intervals_mv
    Market metrics always use market_summary.
    """
    if metric_def.source_table == TABLE_MARKET_SUMMARY:
        return TABLE_MARKET_SUMMARY
    return _get_source_table_for_grouping(grouping)


def get_value_expression(metric_def: MetricDefinition, period: MilestonePeriod) -> tuple[str, str]:
    """Get the value column and aggregation function for a metric + period.

    Handles special cases like demand switching from AVG(demand) at interval
    to SUM(demand_energy) at day+.

    Returns (value_column, agg_function)
    """
    if metric_def.metric == MilestoneType.demand:
        if period == MilestonePeriod.interval:
            return "demand", "AVG"
        return "demand_energy", "SUM"

    return metric_def.value_column, metric_def.agg_function
