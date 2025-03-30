"""
Bulk analysis of milestone records.

This module analyzes data from ClickHouse tables to find milestone records (highs and lows)
across different metrics, networks, periods and grouping configurations.

The live engine which runs per interval is located at opennem.recordreactor.engine
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from textwrap import dedent
from typing import Any

from clickhouse_driver.client import Client
from sqlalchemy import func, select, text

from opennem.db import get_read_session, get_write_session
from opennem.db.clickhouse import get_clickhouse_client
from opennem.db.models.opennem import Milestones
from opennem.queries.utils import list_to_case
from opennem.recordreactor.persistence import check_and_persist_milestones_chunked
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestonePeriod,
    MilestoneRecordSchema,
    MilestoneType,
)
from opennem.recordreactor.unit import get_milestone_unit
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.recordreactor.backlog")


@dataclass
class IntervalThresholds:
    """Minimum number of intervals required for each period bucket to be considered valid minimum record"""

    interval: int = 1
    day: int = 288  # day has to be complete for a min record to be valid
    week: int = 2016  # week has to be complete for a min record to be valid
    week_rolling: int = 2016  # week has to be complete for a min record to be valid
    month: int = 8000  # some leeway with months since we have missing intervals in every early month
    quarter: int = 24000
    year: int = 98000
    financial_year: int = 98000

    def get_for_period(self, period: MilestonePeriod) -> int:
        """Get threshold for a given period"""
        return getattr(self, period.value)


# Create a global instance for use in queries
INTERVAL_THRESHOLDS = IntervalThresholds()


@dataclass
class GroupingConfig:
    """Configuration for how to group generation records"""

    name: str
    group_by_fields: list[str] | None


# Define all possible grouping configurations
_GROUPING_CONFIGS = [
    GroupingConfig(name="network", group_by_fields=[]),
    GroupingConfig(name="region", group_by_fields=["network_region"]),
    GroupingConfig(name="fueltech", group_by_fields=["fueltech_group_id"]),
    GroupingConfig(name="renewable", group_by_fields=["renewable"]),
    GroupingConfig(name="region_fueltech", group_by_fields=["network_region", "fueltech_group_id"]),
    GroupingConfig(name="region_renewable", group_by_fields=["network_region", "renewable"]),
]


def get_time_bucket_sql(period: MilestonePeriod, source_table: str = "unit_intervals_daily_mv", time_col: str = "date") -> str:
    """Generate SQL for different time bucket periods."""

    if period == MilestonePeriod.interval:
        return f"{source_table}.{time_col}"
    elif period == MilestonePeriod.day:
        return f"toStartOfDay({source_table}.{time_col})"
    elif period == MilestonePeriod.week:
        return f"toStartOfWeek({source_table}.{time_col})"
    elif period == MilestonePeriod.week_rolling:
        return f"toStartOfWeek({source_table}.{time_col})"
    elif period == MilestonePeriod.month:
        return f"toStartOfMonth({source_table}.{time_col})"
    elif period == MilestonePeriod.quarter:
        return f"toStartOfQuarter({source_table}.{time_col})"
    elif period == MilestonePeriod.year:
        return f"toStartOfYear({source_table}.{time_col})"
    elif period == MilestonePeriod.financial_year:
        return f"""
            if(
                toMonth({source_table}.{time_col}) >= 7,
                toStartOfYear({source_table}.{time_col}) + interval '1 year',
                toStartOfYear({source_table}.{time_col})
            )
        """
    else:
        raise ValueError(f"Unsupported period: {period}")


def _get_source_table_and_interval_name(
    milestone_type: MilestoneType, period: MilestonePeriod, grouping: GroupingConfig
) -> tuple[str, str]:
    if milestone_type in [MilestoneType.power, MilestoneType.energy, MilestoneType.emissions, MilestoneType.market_value]:
        if "fueltech_group_id" in grouping.group_by_fields:
            return "fueltech_intervals_mv", "interval"
            # if period == MilestonePeriod.interval:
            #     return "fueltech_intervals_mv", "interval"
            # else:
            #     return "fueltech_intervals_daily_mv", "date"
        elif "renewable" in grouping.group_by_fields:
            return "renewable_intervals_mv", "interval"
            # if period == MilestonePeriod.interval:
            # else:
            #     return "renewable_intervals_daily_mv", "date"
        else:
            return "fueltech_intervals_mv", "interval"
            # if period == MilestonePeriod.interval:
            # else:
            #     return "fueltech_intervals_daily_mv", "date"
    elif milestone_type in [MilestoneType.price, MilestoneType.demand]:
        return "market_summary", "interval"
    else:
        raise ValueError(f"Unsupported milestone type: {milestone_type}")


def _trim_end_date(time_col: str, end_date: datetime, period: MilestonePeriod) -> str:
    """
    Generate SQL condition to trim end date to last complete period.

    Args:
        time_col: The column name containing the timestamp
        end_date: The end date to trim
        period: The period type to trim to

    Returns:
        str: SQL condition for the trimmed end date
    """
    end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
    end_date_dt = f"toDateTime('{end_date_str}')"

    if period == MilestonePeriod.day:
        return f"{time_col} < toStartOfDay({end_date_dt})"
    elif period == MilestonePeriod.week:
        return f"{time_col} < toStartOfWeek({end_date_dt})"
    elif period == MilestonePeriod.week_rolling:
        return f"{time_col} < toStartOfWeek({end_date_dt})"
    elif period == MilestonePeriod.month:
        return f"{time_col} < toStartOfMonth({end_date_dt})"
    elif period == MilestonePeriod.quarter:
        return f"{time_col} < toStartOfQuarter({end_date_dt})"
    elif period == MilestonePeriod.year:
        return f"{time_col} < toStartOfYear({end_date_dt})"
    elif period == MilestonePeriod.financial_year:
        return f"""
            {time_col} < if(
                toMonth({end_date_dt}) >= 7,
                toStartOfYear({end_date_dt}) + interval '1 year',
                toStartOfYear({end_date_dt})
            )
        """
    else:
        # For interval period or any other, use the exact end date
        return f"{time_col} < {end_date_dt}"


def _analyze_milestone_records(
    client: Client,
    network: NetworkSchema,
    period: MilestonePeriod,
    milestone_type: MilestoneType,
    grouping: GroupingConfig,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    debug: bool = False,
) -> list[dict[str, Any]]:
    """
    Analyze historical records to find milestone records.

    This function handles both generation and market summary records based on the milestone type.
    For generation records (power, energy, emissions) it uses SUM aggregation.
    For market records (price, demand) it uses AVG aggregation.

    Args:
        client: ClickHouse client
        network: Network to analyze
        period: Period bucket to analyze
        milestone_type: Type of milestone to find
        grouping: How to group the records
        start_date: Optional start date to limit analysis
        end_date: Optional end date to limit analysis

    Returns:
        list[dict[str, Any]]: List of milestone records
    """

    # skip WEM region queries
    if network == NetworkWEM and "network_region" in grouping.group_by_fields:
        return []

    source_table, time_col = _get_source_table_and_interval_name(milestone_type, period, grouping)
    time_bucket_sql = get_time_bucket_sql(period, source_table, time_col)
    # interval_threshold = INTERVAL_THRESHOLDS.get_for_period(period)

    # Build the GROUP BY clause from the configuration
    group_by_fields = []

    if grouping.group_by_fields:
        group_by_fields.extend(grouping.group_by_fields)

    # Build partition fields for window functions
    partition_fields = []

    if grouping.group_by_fields:
        partition_fields = [f for f in grouping.group_by_fields if f != "network_id"]

    partition_clause = ", ".join(partition_fields) if partition_fields else "1"

    # Handle group by fields in SELECT statements
    group_by_select = ""
    if grouping.group_by_fields:
        # Special handling for renewable grouping
        mapped_fields = []
        for field in grouping.group_by_fields:
            mapped_fields.append(field)
        group_by_select = f", {', '.join(mapped_fields)}"

    # convert the metric to the column name and determine aggregation
    metric_column = ""

    # Determine aggregation function and value column name
    agg_function = "SUM"

    # interval count value
    interval_count = "max(interval_count)"

    # if period == MilestonePeriod.interval:
    interval_count = "1"

    if milestone_type == MilestoneType.power:
        metric_column = "generated"
    elif milestone_type == MilestoneType.energy:
        metric_column = "energy"
    elif milestone_type == MilestoneType.emissions:
        metric_column = "emissions"
    elif milestone_type == MilestoneType.market_value:
        metric_column = "market_value"
    elif milestone_type == MilestoneType.price:
        interval_count = "1"
        if period == MilestonePeriod.interval:
            metric_column = "price"
            agg_function = "AVG"
        else:
            raise ValueError("Price records are only supported at the interval period")
    elif milestone_type == MilestoneType.demand:
        interval_count = "1"
        if period == MilestonePeriod.interval:
            metric_column = "demand"
            agg_function = "AVG"
        else:
            metric_column = "demand_energy"
            agg_function = "SUM"

    if not metric_column:
        raise ValueError(f"Unsupported milestone type: {milestone_type}")

    # Build date range conditions
    date_conditions = []
    if start_date:
        date_conditions.append(f"{time_col} >= toDateTime('{start_date.strftime('%Y-%m-%d %H:%M:%S')}')")
    if end_date:
        date_conditions.append(_trim_end_date(time_col, end_date, period))

    date_clause = f"AND {' AND '.join(date_conditions)}" if date_conditions else ""

    # get the min value for the period
    interval_threshold = INTERVAL_THRESHOLDS.get_for_period(period)
    # interval_threshold = 1

    # get the lowest max value for the period and metric type
    maxes_min_value = 100

    if milestone_type in [MilestoneType.energy, MilestoneType.emissions]:
        maxes_min_value = 1000

    # value limit. 0 is the default but for values that can go negative we exclude it
    value_limit_clause = "" if milestone_type in [MilestoneType.price] else "total_value > 0 and "

    # date cutoffs for certain metrics
    date_cutoffs = "and time_bucket >= toDateTime('2000-01-01')"

    if milestone_type in [MilestoneType.price, MilestoneType.demand]:
        date_cutoffs = "and time_bucket >= toDateTime('2009-07-01')"

    base_query = f"""
    WITH base_stats AS (
      SELECT
        {time_bucket_sql} as time_bucket{group_by_select},
        {interval_count} as interval_count,
        {agg_function}({metric_column}) as total_value
      FROM {source_table} FINAL
      WHERE
        network_id in ('{network.code.upper()}', {list_to_case([i.code for i in network.subnetworks])})
        {date_clause}
        {date_cutoffs}
      GROUP BY
        {time_bucket_sql}{group_by_select}
      ORDER BY 1 asc, 2
    ),

    running_maxes AS (
      SELECT
        time_bucket{group_by_select},
        total_value,
        interval_count,
        max(total_value) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as running_max,
        generateUUIDv7() as instance_id
      FROM base_stats
      WHERE round(total_value, 0) > {maxes_min_value}
    ),

    max_records AS (
      SELECT
        time_bucket{group_by_select},
        total_value,
        interval_count,
        running_max,
        instance_id,
        lagInFrame(running_max) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as prev_max,
        lagInFrame(instance_id) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as prev_instance_id
      FROM running_maxes
    ),

    running_mins AS (
      SELECT
        time_bucket{group_by_select},
        total_value,
        interval_count,
        min(
          if(
            {value_limit_clause} interval_count >= {interval_threshold},
            total_value,
            NULL
          )
        ) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as running_min,
        generateUUIDv7() as instance_id
      FROM base_stats
    ),

    min_records AS (
      SELECT
        time_bucket{group_by_select},
        total_value,
        interval_count,
        running_min,
        instance_id,
        lagInFrame(running_min) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as prev_min,
        lagInFrame(instance_id) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as prev_instance_id
      FROM running_mins
    )

    SELECT *
    FROM (
      SELECT
        time_bucket as interval{group_by_select},
        total_value,
        interval_count,
        if(
          prev_max IS NULL,
          0,
          ((total_value - prev_max) / prev_max) * 100
        ) as pct_change,
        'high' as record_type,
        '{period.value}' as period,
        instance_id,
        prev_instance_id
      FROM max_records
      WHERE
        total_value = running_max
        AND (prev_max IS NULL OR total_value > prev_max)

      UNION ALL

      SELECT
        time_bucket as interval{group_by_select},
        total_value,
        interval_count,
        if(
          prev_min IS NULL,
          0,
          ((total_value - prev_min) / prev_min) * 100
        ) as pct_change,
        'low' as record_type,
        '{period.value}' as period,
        instance_id,
        prev_instance_id
      FROM min_records
      WHERE
        total_value = running_min
        AND (prev_min IS NULL OR total_value < prev_min AND interval_count >= {interval_threshold})
    )
    ORDER BY interval"""

    try:
        logger.info(f"running query for {network.code} {milestone_type.value} {period.value} {grouping.name}")

        if debug:
            print(dedent(base_query))

        records = client.execute(base_query)
        # Convert to list of dicts for easier processing
        field_names = [
            "interval",
            *(list(grouping.group_by_fields) if grouping.group_by_fields else []),
            "total_value",
            "interval_count",
            "pct_change",
            "record_type",
            "period",
            "instance_id",
            "prev_instance_id",
        ]

        records = [dict(zip(field_names, record, strict=False)) for record in records]

        return records

    except Exception as e:
        logger.error(f"Error during milestone analysis: {str(e)}")
        raise


def _analyzed_record_to_milestone_schema(
    records: list[dict[str, Any]],
    network: NetworkSchema,
    period: MilestonePeriod,
    milestone_type: MilestoneType,
    grouping: GroupingConfig,
) -> list[MilestoneRecordSchema]:
    """
    Convert analyzed records to milestone record schemas.
    """
    unit = get_milestone_unit(milestone_type)
    milestone_records = []
    milestone_primary_keys: list[set(str, str)] = []  # type: ignore

    for record in records:
        milestone_type_out = milestone_type

        # Get network region and fueltech from grouping if present
        network_region = record.get("network_region") if "network_region" in record else None
        fueltech = None

        if "fueltech_group_id" in record:
            fueltech = MilestoneFueltechGrouping(record["fueltech_group_id"])
        elif "renewable" in record:
            fueltech = MilestoneFueltechGrouping("renewables" if record["renewable"] else "fossils")

        if milestone_type == MilestoneType.demand:
            fueltech = MilestoneFueltechGrouping.demand
            milestone_type_out = MilestoneType.energy
            if period == MilestonePeriod.interval:
                milestone_type_out = MilestoneType.power

        value = record.get("total_value", record.get("total_generation"))

        # Only include previous_instance_id if it's not NULL
        previous_instance_id = record["prev_instance_id"] if record["prev_instance_id"] else None

        milestone_schema = MilestoneRecordSchema(
            interval=record["interval"],
            aggregate=MilestoneAggregate(record["record_type"]),
            metric=milestone_type_out,
            period=period,
            network=network,
            unit=unit,
            network_region=network_region,
            fueltech=fueltech,
            value=value,
            pct_change=round(record["pct_change"], 2)
            if record["pct_change"] and (abs(record["pct_change"]) < 9999 and abs(record["pct_change"]) > 0.01)
            else None,
            instance_id=record["instance_id"],
            previous_instance_id=previous_instance_id,
        )

        # track primary keys and error if there is a duplicate
        primary_keys = (milestone_schema.interval, milestone_schema.instance_id)

        if primary_keys in milestone_primary_keys:
            logger.info(milestone_schema)
            raise ValueError(f"Duplicate milestone record: {primary_keys}")

        # skip solar records before 26 October 2015 because of backfill
        if fueltech in [
            MilestoneFueltechGrouping.solar,
        ] and milestone_schema.interval < datetime.fromisoformat("2015-10-26T00:00:00"):
            continue

        # skip renewables records before 2014 because of backfill
        if fueltech in [MilestoneFueltechGrouping.renewables] and milestone_schema.interval < datetime.fromisoformat(
            "2010-01-01T00:00:00"
        ):
            continue

        # skip wind before we had non-scheduled generation data
        if fueltech in [MilestoneFueltechGrouping.wind] and milestone_schema.interval < datetime.fromisoformat(
            "2009-07-01T00:00:00"
        ):
            continue

        milestone_primary_keys.append(primary_keys)

        milestone_records.append(milestone_schema)

    return milestone_records


_DEFAULT_PERIODS = [
    MilestonePeriod.interval,
    MilestonePeriod.day,
    # MilestonePeriod.week,
    # MilestonePeriod.week_rolling,
    MilestonePeriod.month,
    MilestonePeriod.quarter,
    MilestonePeriod.year,
]

_DEFAULT_METRICS = [
    MilestoneType.demand,
    MilestoneType.price,
    MilestoneType.power,
    MilestoneType.energy,
    MilestoneType.emissions,
    # MilestoneType.market_value,
]

_DEFAULT_NETWORKS = [
    NetworkNEM,
    NetworkWEM,
]


async def run_milestone_analysis(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    networks: list[NetworkSchema] | None = None,
    metrics: list[MilestoneType] | None = None,
    periods: list[MilestonePeriod] | None = None,
    groupings: list[GroupingConfig] | None = None,
    debug: bool = False,
) -> None:
    """
    Run milestone analysis across all grouping configurations.

    Args:
        start_date: Optional start date to limit analysis
        end_date: Optional end date to limit analysis
        networks: Optional list of networks to analyze
        metrics: Optional list of metrics to analyze
        periods: Optional list of periods to analyze
        groupings: Optional list of grouping configurations to analyze
        debug: Optional flag to enable debug mode
    """
    client = get_clickhouse_client()

    # Iterate through all periods and grouping configurations
    for metric in metrics or _DEFAULT_METRICS:
        for network in networks or _DEFAULT_NETWORKS:
            for period in periods or _DEFAULT_PERIODS:
                milestone_records: list[MilestoneRecordSchema] = []

                for grouping in groupings or _GROUPING_CONFIGS:
                    # filter out the metrics that don't make sense for the period

                    if metric in [MilestoneType.power, MilestoneType.energy, MilestoneType.emissions]:
                        if period == MilestonePeriod.interval and metric not in [MilestoneType.power]:
                            continue

                        if period != MilestonePeriod.interval and metric == MilestoneType.power:
                            continue

                    if metric in [MilestoneType.price]:
                        if period != MilestonePeriod.interval:
                            continue

                    if metric in [MilestoneType.demand, MilestoneType.price]:
                        # Skip fueltech-related groupings for market summary records
                        if grouping.name in [
                            "fueltech",
                            "region_fueltech",
                            "renewable",
                            "region_renewable",
                        ]:
                            continue

                    records = _analyze_milestone_records(
                        client=client,
                        network=network,
                        milestone_type=metric,
                        period=period,
                        grouping=grouping,
                        start_date=start_date,
                        end_date=end_date,
                        debug=debug,
                    )

                    milestone_records.extend(_analyzed_record_to_milestone_schema(records, network, period, metric, grouping))

                if milestone_records:
                    logger.info(
                        f"Found {len(milestone_records)} milestone records for {network.code} {metric.value} {period.value}"
                    )

                    await check_and_persist_milestones_chunked(milestone_records)

    logger.info("Milestone analysis complete")


async def run_milestone_analysis_backlog(refresh: bool = False, debug: bool = False):
    """
    Runs in year chunks
    """
    end_date = get_last_completed_interval_for_network(NetworkNEM)
    start_date = NetworkNEM.data_first_seen.replace(tzinfo=None)
    # start_date = end_date - timedelta(days=90)

    if refresh:
        async with get_write_session() as session:
            await session.execute(text("delete from milestones"))
        logger.info("Milestones table deleted")

    await run_milestone_analysis(start_date=start_date, end_date=end_date, debug=debug)


async def run_update_milestone_analysis_to_now() -> None:
    """
    Run milestone analysis from the last recorded milestone to now.

    This function queries the max interval from the milestones table and runs the analysis
    from that date to the current time.
    """
    async with get_read_session() as session:
        # Get the max interval from milestones table
        query = select(func.max(Milestones.interval))
        result = await session.execute(query)
        last_milestone_date = result.scalar()

        if not last_milestone_date:
            logger.warning("No existing milestones found. Run full backlog analysis.")
            return

        logger.info(f"Running milestone analysis from {last_milestone_date} to now")
        end_date = get_last_completed_interval_for_network(NetworkNEM)

        await run_milestone_analysis(start_date=last_milestone_date, end_date=end_date)

        logger.info("Milestone update analysis complete")


if __name__ == "__main__":
    # Run test for last year of data
    import asyncio

    async def _test_analyze_milestone_records():
        await run_milestone_analysis(
            metrics=[MilestoneType.power],
            periods=[MilestonePeriod.interval],
            groupings=[GroupingConfig(name="fueltech", group_by_fields=["fueltech_group_id"])],
            networks=[NetworkNEM],
            debug=True,
        )

    async def test():
        await run_milestone_analysis_backlog(refresh=True)

    asyncio.run(test())
