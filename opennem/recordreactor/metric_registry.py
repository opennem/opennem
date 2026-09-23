"""
Declarative metric configuration for milestone record detection.

Replaces scattered conditionals in backlog.py with a single registry that defines
every valid (metric, period, grouping) combination, their source tables, column mappings,
aggregation functions, and value constraints.
"""

from dataclasses import dataclass, field
from datetime import datetime

from opennem.queries.utils import list_to_case
from opennem.recordreactor.schema import MilestoneFueltechGrouping, MilestonePeriod, MilestoneType
from opennem.schema.network import NetworkSchema, NetworkWEM

# Source table constants
TABLE_FUELTECH_INTERVALS = "fueltech_intervals_mv"
TABLE_RENEWABLE_INTERVALS = "renewable_intervals_mv"
TABLE_MARKET_SUMMARY = "market_summary"

# Renewable proportion, bounded at 200%. Values above come from a near-zero demand_gross
# denominator (a data artifact, GH #558) and return -1 so the `total_value > 0` filters in the
# record CTEs drop them. Legit >100% net-exporter intervals pass through.
#
# This is no longer the primary guard: `get_proportion_sql` makes the proportion NULL unless every
# input is present for every region and interval of the bucket (#662). The clamp stays as a
# last-resort bound on complete data.
PROPORTION_CLAMPED_SQL = (
    "round(if(sum(demand_gross) > 0 "
    "AND (sum(generation_renewable) / sum(demand_gross)) * 100 <= 200, "
    "(sum(generation_renewable) / sum(demand_gross)) * 100, -1), 2)"
)


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


# Fueltech groupings derived from the renewable flag rather than a fueltech_group_id column
_RENEWABLE_FLAG_GROUPINGS = (MilestoneFueltechGrouping.renewables.value, MilestoneFueltechGrouping.fossils.value)


def get_fueltech_date_cutoffs() -> dict[str, datetime]:
    """Earliest date each fueltech grouping has usable data.

    Single source of truth for both detection paths — the backlog used to carry its own hardcoded
    copy of these dates (#656).
    """
    return _FUELTECH_DATE_CUTOFFS


# Regions that were part of a network but are no longer declared on it. Mirrors
# aggregates.market_summary._HISTORIC_NETWORK_REGIONS: SNOWY1 was a NEM region until July 2008
# and carries real demand in market_summary.
_HISTORIC_NETWORK_REGIONS: dict[str, list[str]] = {"NEM": ["SNOWY1"]}


def get_network_region_filter_sql(network: NetworkSchema) -> str:
    """SQL keeping only rows in the network's own regions (declared plus historic).

    Record queries select a network by network_id plus its subnetworks, and a subnetwork can carry
    regions outside the network: the OPENNEM_ROOFTOP_BACKFILL rooftop has NT1 rows (2015-10 to
    2016-08), which minted au.nem.nt1.* record chains and added NT rooftop into NEM totals. It
    also drops market_summary's known-bad network_id NEM / network_region WEM rows.

    Returns "" for a network with no declared regions.
    """
    regions = list(network.regions or []) + _HISTORIC_NETWORK_REGIONS.get(network.code, [])

    if not regions:
        return ""

    return f"and network_region IN ({list_to_case(regions)})"


def get_fueltech_cutoff_sql(group_by_fields: list[str] | None, time_expression: str) -> str:
    """SQL excluding buckets before a fueltech's data-quality cutoff.

    This belongs in the WHERE of the aggregation, not in a filter over its output. The backlog
    computed its running extremes over all history and then dropped the pre-cutoff records
    afterwards, so a series whose lows all sit at the start of its history — solar and wind both
    do, they only grow — had every low it found discarded and was written to the table with an
    empty low chain. The live checker then minted the next value it saw as an all-time low (#656).

    Returns "" for a grouping with no fueltech key: a network or region total has no single
    fueltech to cut off.
    """
    fields = group_by_fields or []
    clauses: list[str] = []

    if "fueltech_group_id" in fields:
        for fueltech, cutoff in _FUELTECH_DATE_CUTOFFS.items():
            if fueltech in _RENEWABLE_FLAG_GROUPINGS:
                continue
            clauses.append(
                f"NOT (fueltech_group_id = '{fueltech}' "
                f"AND {time_expression} < toDateTime('{cutoff.strftime('%Y-%m-%d %H:%M:%S')}'))"
            )

    if "renewable" in fields:
        cutoff = _FUELTECH_DATE_CUTOFFS.get(MilestoneFueltechGrouping.renewables.value)
        if cutoff:
            clauses.append(f"NOT (renewable = 1 AND {time_expression} < toDateTime('{cutoff.strftime('%Y-%m-%d %H:%M:%S')}'))")

    if not clauses:
        return ""

    return "and " + "\n        and ".join(clauses)


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
        agg_function="SUM",  # market_summary holds one row per (interval, network_region)
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
        # the clamped expression alone; queries wrap it in the completeness guard from
        # get_proportion_sql (#662)
        value_column=PROPORTION_CLAMPED_SQL,
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


# Generation metrics whose totals roll rooftop solar in with grid generation
_GENERATION_METRICS = (MilestoneType.power, MilestoneType.energy, MilestoneType.emissions)


def _rooftop_rows(metric: MilestoneType, group_by_fields: list[str] | None) -> bool | tuple[str, str | int]:
    """Which rows of a (metric, grouping) query can contain rooftop solar.

    True: every row. False: none. (column, value): the rows where `column = value`.

    The single definition behind both `row_contains_rooftop` (the incremental path, per row in
    Python) and `get_rooftop_settled_sql` (the backlog, per row in SQL), so the two can't drift
    (#662).
    """
    fields = group_by_fields or []

    if metric == MilestoneType.proportion:
        # rooftop is in both generation_renewable and demand_gross
        return True

    if metric not in _GENERATION_METRICS:
        # demand is operational demand (rooftop excluded); price has no generation in it
        return False

    if "fueltech_group_id" in fields:
        return ("fueltech_group_id", MilestoneFueltechGrouping.solar.value)

    if "renewable" in fields:
        return ("renewable", 1)

    # network and region totals have no fueltech filter, so rooftop is in them
    return True


def row_contains_rooftop(metric_def: MetricDefinition, grouping: GroupingConfig, row: dict) -> bool:
    """Whether an aggregated row's value can contain rooftop solar.

    Rooftop lands 30 minutes to two hours after the interval it covers, so only these rows are
    partial until it settles (#652). Everything else — coal, gas, hydro, wind, batteries, pumps,
    fossils, operational demand, price — is complete as soon as the grid data arrives and must not
    be held back.

    Note this is a per-ROW test, not a per-query one: the fueltech grouping returns solar next to
    coal, and the renewable grouping returns renewables next to fossils, in the same result set.
    """
    rows = _rooftop_rows(metric_def.metric, grouping.group_by_fields)

    if isinstance(rows, bool):
        return rows

    column, value = rows

    if column == "renewable":
        return bool(row.get(column)) == bool(value)

    return row.get(column) == value


def get_rooftop_settled_sql(
    metric: MilestoneType,
    group_by_fields: list[str] | None,
    time_expression: str,
    settled_interval: datetime,
) -> str:
    """SQL excluding rows that can contain rooftop solar after the last settled interval.

    The backlog (full rebuild, gap backfill, reconciliation) ran every interval series to the last
    completed interval, so the most recent hour or two of any series with rooftop in it was summed
    on grid-only generation. That is how the false vic1 generation interval lows got in, and a
    rebuild would have minted them again (#662). This is the backlog's version of the per-row gate
    the incremental path applies in `row_contains_rooftop` (#652), built from the same definition.

    Like `get_fueltech_cutoff_sql` it belongs in the WHERE of the aggregation, so the running
    extremes never see the partial rows — not in a filter over the output (#654, #656). Only for
    the interval period: day+ buckets are trimmed to the last complete bucket and rooftop has long
    landed by then.

    Returns "" when no row of the query can contain rooftop.
    """
    rows = _rooftop_rows(metric, group_by_fields)

    if rows is False:
        return ""

    settled_dt = f"toDateTime('{settled_interval.strftime('%Y-%m-%d %H:%M:%S')}')"

    if rows is True:
        # every row carries rooftop: the whole query ends at the settled interval
        return f"and {time_expression} <= {settled_dt}"

    column, value = rows
    value_sql = f"'{value}'" if isinstance(value, str) else str(value)

    return f"and NOT ({column} = {value_sql} AND {time_expression} > {settled_dt})"


# WEM ran 30-minute trading intervals until the WEMDE cutover (NetworkWEMDE.data_first_seen, in
# WEM network time). The network schema only knows the 5-minute size, so the expected interval
# count for a bucket that starts before this can't be derived; those buckets keep the old
# behaviour (no completeness count) rather than being rejected wholesale.
_WEM_FIVE_MINUTE_FROM = datetime.fromisoformat("2023-10-01T08:00:00")

_PERIOD_SQL_INTERVAL = {
    MilestonePeriod.day: "DAY",
    MilestonePeriod.week: "WEEK",
    MilestonePeriod.month: "MONTH",
    MilestonePeriod.quarter: "QUARTER",
    MilestonePeriod.year: "YEAR",
}


def get_expected_intervals_sql(period: MilestonePeriod, time_bucket_sql: str, interval_size: int) -> str:
    """SQL for how many network intervals a bucket holds: 288 for a day at 5 minutes.

    Network time is a fixed offset with no DST, so this is the bucket's length in minutes over the
    interval size, computed from the bucket itself so a 28-day February and a leap year get their
    real counts rather than the loose `_DEFAULT_INTERVAL_THRESHOLDS`.
    """
    if period == MilestonePeriod.interval:
        return "1"

    unit = _PERIOD_SQL_INTERVAL.get(period)

    if not unit:
        raise ValueError(f"No expected interval count for period {period}")

    return f"intDiv(dateDiff('minute', {time_bucket_sql}, {time_bucket_sql} + INTERVAL 1 {unit}), {interval_size})"


def get_proportion_sql(
    network: NetworkSchema,
    group_by_fields: list[str] | None,
    period: MilestonePeriod,
    time_col: str,
    time_bucket_sql: str,
) -> tuple[str, str]:
    """(value, interval_count) SQL for renewable proportion, NULL unless its inputs are complete.

    market_summary leaves demand_gross and generation_renewable NULL for a region and interval
    when any input (rooftop, demand_total, scada) is missing (#661). sum() silently skips NULLs,
    so a network proportion over four of five regions, or a day with an hour missing, came out as
    a plausible partial number and could register as a record (#662). The rule is now: NULL
    unless every input is present.

    - interval: every region of the network (the one region, for the region grouping) has both
      columns non-NULL for the interval.
    - day and above: that holds for every interval of the bucket, counted against the bucket's
      real length (`get_expected_intervals_sql`). WEM buckets starting before the 5-minute cutover
      are exempt, see `_WEM_FIVE_MINUTE_FROM`.

    Completeness counts (interval, region) rows among the network's declared regions, so a stray
    region row (the historic SNOWY1, or the known-bad NEM/WEM rows) can't stand in for a missing
    one. It is a plain countIf, not a distinct count: both paths read market_summary FINAL, which
    holds exactly one row per (interval, network_id, network_region), and market_summary only
    carries the NEM and WEM network ids. uniqExactIf gave the same answer but kept a hash set per
    group, and at the interval period (one group per interval and region, ~17M of them over NEM
    history) that alone pushed the rebuild's region query past 4 GB. A NULL value is dropped by
    both paths: the backlog's `total_value > 0` /
    `total_value = running_max` filters and the incremental path's `value is None` check. It
    applies to highs and lows alike.

    The same SQL is used by the backlog and the incremental queries so the two can't disagree.
    interval_count is the number of complete intervals, which equals the expected count exactly
    when the bucket is complete.
    """
    fields = group_by_fields or []
    regions = network.regions or [network.code]
    required_regions = 1 if "network_region" in fields else len(regions)

    complete_pairs = (
        f"countIf(network_region IN ({list_to_case(regions)}) AND demand_gross IS NOT NULL AND generation_renewable IS NOT NULL)"
    )
    expected = get_expected_intervals_sql(period, time_bucket_sql, network.interval_size)
    complete = f"{complete_pairs} = {expected} * {required_regions}"

    if period == MilestonePeriod.interval:
        return f"if({complete}, {PROPORTION_CLAMPED_SQL}, NULL)", "1"

    interval_count = f"intDiv({complete_pairs}, {required_regions})"

    if network == NetworkWEM:
        exempt = f"{time_bucket_sql} < toDateTime('{_WEM_FIVE_MINUTE_FROM.strftime('%Y-%m-%d %H:%M:%S')}')"
        complete = f"({exempt} OR {complete})"
        # both branches cast to UInt64: `expected` is signed (dateDiff) and the count is unsigned,
        # which ClickHouse 25 rejects ("no supertype") and 26 turns into a Variant that base_stats
        # can't ORDER BY. clickhouse local 24.1 in the tests accepts either, so it didn't show there
        interval_count = f"if({exempt}, toUInt64({expected}), toUInt64({interval_count}))"

    return f"if({complete}, {PROPORTION_CLAMPED_SQL}, NULL)", interval_count


def get_value_expression(metric_def: MetricDefinition, period: MilestonePeriod) -> tuple[str, str]:
    """Get the value column and aggregation function for a metric + period.

    Handles special cases like demand switching from SUM(demand) at interval
    to SUM(demand_energy) at day+.

    Demand is always summed. `market_summary` holds exactly one row per
    (interval, network_region), so SUM is identical to AVG for the region grouping and is the
    only correct choice for the network grouping, which has no region key: AVG returned the mean
    of the five NEM regions, publishing nem-wide demand lows at a fifth of the real value (#653).
    Price stays AVG — the mean across regions is the intended definition there.

    Returns (value_column, agg_function)
    """
    if metric_def.metric == MilestoneType.demand:
        if period == MilestonePeriod.interval:
            return "demand", "SUM"
        return "demand_energy", "SUM"

    return metric_def.value_column, metric_def.agg_function
