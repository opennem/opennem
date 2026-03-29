"""
Simple ClickHouse aggregation queries for incremental milestone detection.

No window functions — each query aggregates a single completed period and returns
one value per grouping key. Python handles comparison against current state.
"""

import logging
from datetime import datetime
from typing import Any

from opennem.queries.utils import list_to_case
from opennem.recordreactor.metric_registry import (
    GroupingConfig,
    MetricDefinition,
    get_source_table_for_metric_grouping,
    get_value_expression,
)
from opennem.recordreactor.schema import MilestonePeriod
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.recordreactor.queries_incremental")


def _get_time_bucket_sql(period: MilestonePeriod, time_col: str) -> str:
    """Generate ClickHouse time bucket expression for a period"""
    if period == MilestonePeriod.interval:
        return time_col
    elif period == MilestonePeriod.day:
        return f"toStartOfDay({time_col})"
    elif period == MilestonePeriod.week:
        return f"toStartOfWeek({time_col})"
    elif period == MilestonePeriod.month:
        return f"toStartOfMonth({time_col})"
    elif period == MilestonePeriod.quarter:
        return f"toStartOfQuarter({time_col})"
    elif period == MilestonePeriod.year:
        return f"toStartOfYear({time_col})"
    elif period == MilestonePeriod.financial_year:
        return f"""if(
            toMonth({time_col}) >= 7,
            toStartOfYear({time_col}) + interval '1 year',
            toStartOfYear({time_col})
        )"""
    else:
        raise ValueError(f"Unsupported period: {period}")


def _build_network_filter(network: NetworkSchema, time_col: str) -> str:
    """Build WHERE clause for network filtering"""
    network_codes = [network.code.upper()]
    if network.subnetworks:
        network_codes.extend([s.code for s in network.subnetworks])
    return f"network_id IN ({list_to_case(network_codes)})"


def build_period_aggregation_query(
    metric_def: MetricDefinition,
    network: NetworkSchema,
    grouping: GroupingConfig,
    period: MilestonePeriod,
    period_start: datetime,
    period_end: datetime,
) -> str:
    """Build a simple aggregation query for one completed period.

    Returns a ClickHouse SQL query that aggregates metrics over the period
    grouped by the specified fields.
    """
    source_table = get_source_table_for_metric_grouping(metric_def, grouping)
    time_col = metric_def.time_col
    value_col, agg_func = get_value_expression(metric_def, period)

    # Build SELECT fields
    time_bucket = _get_time_bucket_sql(period, time_col)
    select_fields = [f"{time_bucket} as time_bucket"]
    group_by_fields = [time_bucket]

    if grouping.group_by_fields:
        select_fields.extend(grouping.group_by_fields)
        group_by_fields.extend(grouping.group_by_fields)

    # Build value expression
    if agg_func:
        select_fields.append(f"{agg_func}({value_col}) as value")
    else:
        # Pre-computed expression (e.g., proportion)
        select_fields.append(f"{value_col} as value")

    # Add interval count for LOW record validation
    if period != MilestonePeriod.interval:
        select_fields.append(f"count(distinct {time_col}) as interval_count")
    else:
        select_fields.append("1 as interval_count")

    select_clause = ", ".join(select_fields)
    group_by_clause = ", ".join(group_by_fields)

    # Build WHERE clause
    network_filter = _build_network_filter(network, time_col)
    start_str = period_start.strftime("%Y-%m-%d %H:%M:%S")
    end_str = period_end.strftime("%Y-%m-%d %H:%M:%S")

    # Date cutoff for the metric
    date_cutoff_clause = ""
    if metric_def.date_cutoff:
        cutoff_str = metric_def.date_cutoff.strftime("%Y-%m-%d %H:%M:%S")
        date_cutoff_clause = f"AND {time_col} >= toDateTime('{cutoff_str}')"

    query = f"""
    SELECT {select_clause}
    FROM {source_table} FINAL
    WHERE {network_filter}
      AND {time_col} >= toDateTime('{start_str}')
      AND {time_col} < toDateTime('{end_str}')
      {date_cutoff_clause}
    GROUP BY {group_by_clause}
    """

    return query


def query_period_aggregates(
    client: Any,
    metric_def: MetricDefinition,
    network: NetworkSchema,
    grouping: GroupingConfig,
    period: MilestonePeriod,
    period_start: datetime,
    period_end: datetime,
) -> list[dict[str, Any]]:
    """Execute a period aggregation query and return results as dicts.

    Returns list of dicts with keys: time_bucket, value, interval_count,
    plus any grouping fields (network_region, fueltech_group_id, renewable).
    """
    query = build_period_aggregation_query(
        metric_def=metric_def,
        network=network,
        grouping=grouping,
        period=period,
        period_start=period_start,
        period_end=period_end,
    )

    try:
        rows = client.execute(query)
    except Exception as e:
        logger.error(f"ClickHouse query failed for {metric_def.metric.value} {period.value} {grouping.name}: {e}")
        return []

    # Map rows to dicts
    field_names = ["time_bucket", *grouping.group_by_fields, "value", "interval_count"]
    return [dict(zip(field_names, row, strict=False)) for row in rows]


def query_all_groupings_for_period(
    client: Any,
    metric_def: MetricDefinition,
    network: NetworkSchema,
    period: MilestonePeriod,
    period_start: datetime,
    period_end: datetime,
) -> list[tuple[GroupingConfig, list[dict[str, Any]]]]:
    """Query all valid groupings for a metric + period combination.

    Skips WEM region queries (WEM has no sub-regions).

    Returns list of (grouping, results) tuples.
    """
    from opennem.schema.network import NetworkWEM

    results: list[tuple[GroupingConfig, list[dict[str, Any]]]] = []

    for grouping in metric_def.groupings:
        # Skip WEM region queries — WEM has no sub-regions
        if network == NetworkWEM and "network_region" in grouping.group_by_fields:
            continue

        rows = query_period_aggregates(
            client=client,
            metric_def=metric_def,
            network=network,
            grouping=grouping,
            period=period,
            period_start=period_start,
            period_end=period_end,
        )

        if rows:
            results.append((grouping, rows))

    return results
