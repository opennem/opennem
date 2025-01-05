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

from opennem.db.clickhouse import get_clickhouse_client
from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestonePeriod,
    MilestoneRecordSchema,
    MilestoneType,
)
from opennem.recordreactor.unit import get_milestone_unit
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.recordreactor.bulk")


@dataclass
class IntervalThresholds:
    """Minimum number of intervals required for each period bucket to be considered valid minimum record"""

    interval: int = 1
    day: int = 288  # day has to be complete for a min record to be valid
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
GROUPING_CONFIGS = [
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
    if milestone_type in [MilestoneType.power, MilestoneType.energy, MilestoneType.emissions]:
        if "fueltech_group_id" in grouping.group_by_fields:
            if period == MilestonePeriod.interval:
                return "fueltech_intervals_mv", "interval"
            else:
                return "fueltech_intervals_daily_mv", "date"
        elif "renewable" in grouping.group_by_fields:
            if period == MilestonePeriod.interval:
                return "renewable_intervals_mv", "interval"
            else:
                return "renewable_intervals_daily_mv", "date"
        else:
            if period == MilestonePeriod.interval:
                return "fueltech_intervals_mv", "interval"
            else:
                return "fueltech_intervals_daily_mv", "date"
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


def analyze_generation_records(
    client: Client,
    network: NetworkSchema,
    period: MilestonePeriod,
    milestone_type: MilestoneType,
    grouping: GroupingConfig,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Analyze historical generation records using configurable grouping options.
    """
    # For power we use the base table, for others we use the daily materialized view
    source_table, time_col = _get_source_table_and_interval_name(milestone_type, period, grouping)
    time_bucket_sql = get_time_bucket_sql(period, source_table, time_col)
    interval_threshold = INTERVAL_THRESHOLDS.get_for_period(period)

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

    # convert the metric to the column name
    metric_column = ""

    if milestone_type == MilestoneType.power:
        metric_column = "generated"
    elif milestone_type == MilestoneType.energy:
        metric_column = "energy"
    elif milestone_type == MilestoneType.emissions:
        metric_column = "emissions"

    # Build date range conditions
    date_conditions = []
    if start_date:
        date_conditions.append(f"{time_col} >= toDateTime('{start_date.strftime('%Y-%m-%d %H:%M:%S')}')")
    if end_date:
        date_conditions.append(_trim_end_date(time_col, end_date, period))

    date_clause = f"AND {' AND '.join(date_conditions)}" if date_conditions else ""

    base_query = f"""
    WITH regional_generation AS (
      SELECT
        {time_bucket_sql} as time_bucket{group_by_select},
        COUNT(*) as interval_count,
        SUM({metric_column}) as total_generation
      FROM {source_table}
      WHERE
        network_id = '{network.code.upper()}'
        {date_clause}
      GROUP BY
        {time_bucket_sql}{group_by_select}
    ),

    running_maxes AS (
      SELECT
        time_bucket{group_by_select},
        total_generation,
        interval_count,
        max(total_generation) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as running_max
      FROM regional_generation
      WHERE total_generation > 0
    ),

    max_records AS (
      SELECT
        time_bucket{group_by_select},
        total_generation,
        interval_count,
        running_max,
        lagInFrame(running_max) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as prev_max,
        generateUUIDv7() as instance_id,
        ROW_NUMBER() OVER (
          PARTITION BY time_bucket{group_by_select}
          ORDER BY total_generation DESC, interval_count DESC
        ) AS rn
      FROM running_maxes
      WHERE total_generation = running_max
    ),

    running_mins AS (
      SELECT
        time_bucket{group_by_select},
        total_generation,
        interval_count,
        min(
          if(
            total_generation > 0 AND interval_count >= {interval_threshold},
            total_generation,
            NULL
          )
        ) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as running_min
      FROM regional_generation
      WHERE total_generation > 0
    ),

    min_records AS (
      SELECT
        time_bucket{group_by_select},
        total_generation,
        interval_count,
        running_min,
        lagInFrame(running_min) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) as prev_min,
        generateUUIDv7() as instance_id,
        ROW_NUMBER() OVER (
          PARTITION BY time_bucket{group_by_select}
          ORDER BY total_generation ASC, interval_count DESC
        ) AS rn
      FROM running_mins
      WHERE total_generation = running_min
    ),

    -- Add a final CTE to deduplicate records across network and region levels
    final_records AS (
      SELECT
        time_bucket{group_by_select},
        total_generation,
        interval_count,
        if(
          prev_max IS NULL,
          0,
          ((total_generation - prev_max) / prev_max) * 100
        ) as pct_change,
        'high' as record_type,
        '{period.value}' as period,
        instance_id,
        NULL as prev_instance_id,
        ROW_NUMBER() OVER (
          PARTITION BY time_bucket, record_type
          ORDER BY total_generation DESC, interval_count DESC
        ) AS final_rn
      FROM max_records
      WHERE (prev_max IS NULL OR total_generation > prev_max)
        AND rn = 1

      UNION ALL

      SELECT
        time_bucket{group_by_select},
        total_generation,
        interval_count,
        if(
          prev_min IS NULL,
          0,
          ((total_generation - prev_min) / prev_min) * 100
        ) as pct_change,
        'low' as record_type,
        '{period.value}' as period,
        instance_id,
        NULL as prev_instance_id,
        ROW_NUMBER() OVER (
          PARTITION BY time_bucket, record_type
          ORDER BY total_generation ASC, interval_count DESC
        ) AS final_rn
      FROM min_records
      WHERE (prev_min IS NULL OR total_generation < prev_min)
        AND rn = 1
    )

    SELECT
      time_bucket{group_by_select},
      total_generation,
      interval_count,
      pct_change,
      record_type,
      period,
      instance_id,
      prev_instance_id
    FROM final_records
    WHERE final_rn = 1
    ORDER BY time_bucket"""

    try:
        logger.info(
            f"running query for {network.code} {milestone_type.value} {period.value} {grouping.name} and metric {metric_column}"
        )
        print(dedent(base_query))

        records = client.execute(base_query)
        # Convert to list of dicts for easier processing
        field_names = [
            "interval",
            *(list(grouping.group_by_fields) if grouping.group_by_fields else []),
            "total_generation",
            "interval_count",
            "pct_change",
            "record_type",
            "period",
            "instance_id",
            "prev_instance_id",
        ]

        records = [dict(zip(field_names, record, strict=False)) for record in records]

        # debug print first 5 records
        # pprint(records[0])

        return records

    except Exception as e:
        logger.error(f"Error during milestone analysis: {str(e)}")
        raise


def analyze_market_summary_records(
    client: Client,
    network: NetworkSchema,
    period: MilestonePeriod,
    milestone_type: MilestoneType,
    grouping: GroupingConfig,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Analyze market summary records to find milestone records.
    """
    time_bucket_sql = get_time_bucket_sql(period, "market_summary")
    interval_threshold = INTERVAL_THRESHOLDS.get_for_period(period)
    time_col = "interval"  # market_summary table uses interval column

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
    group_by_select = f", {', '.join(grouping.group_by_fields)}" if grouping.group_by_fields else ""

    # convert the metric to the column name
    metric_column = ""

    if milestone_type == MilestoneType.price:
        metric_column = "price"
    elif milestone_type == MilestoneType.demand:
        metric_column = "demand"

    # Build date range conditions
    date_conditions = []
    if start_date:
        date_conditions.append(f"{time_col} >= toDateTime('{start_date.strftime('%Y-%m-%d %H:%M:%S')}')")
    if end_date:
        date_conditions.append(_trim_end_date(time_col, end_date, period))

    date_clause = f"AND {' AND '.join(date_conditions)}" if date_conditions else ""

    base_query = f"""
    WITH market_data AS (
      SELECT
        {time_bucket_sql} as time_bucket{group_by_select},
        COUNT(*) as interval_count,
        AVG({metric_column}) as total_value
      FROM market_summary
      WHERE
        network_id = '{network.code.upper()}'
        AND network_region IN ({', '.join([f"'{i}'" for i in (network.regions or [])])})
        {date_clause}
      GROUP BY
        {time_bucket_sql}{group_by_select}
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
      FROM market_data
      WHERE total_value > 0
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
            total_value > 0 AND interval_count >= {interval_threshold},
            total_value,
            NULL
          )
        ) OVER (
          PARTITION BY {partition_clause}
          ORDER BY time_bucket
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) as running_min,
        generateUUIDv7() as instance_id
      FROM market_data
      WHERE total_value > 0
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
        AND interval_count >= {interval_threshold}
        AND (prev_min IS NULL OR total_value < prev_min)
    )
    ORDER BY interval"""

    try:
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
    milestone_primary_keys: list[set(str, str)] = []

    for record in records:
        # Get network region and fueltech from grouping if present
        network_region = record.get("network_region") if "network_region" in record else None
        fueltech = None

        if "fueltech_group_id" in record:
            fueltech = MilestoneFueltechGrouping(record["fueltech_group_id"])
        elif "renewable" in record:
            fueltech = MilestoneFueltechGrouping("renewables" if record["renewable"] else "fossils")

        value = record.get("total_value", record.get("total_generation"))

        # Only include previous_instance_id if it's not NULL
        previous_instance_id = record["prev_instance_id"] if record["prev_instance_id"] else None

        milestone_schema = MilestoneRecordSchema(
            interval=record["interval"],
            aggregate=MilestoneAggregate(record["record_type"]),
            metric=milestone_type,
            period=period,
            network=network,
            unit=unit,
            network_region=network_region,
            fueltech=fueltech,
            value=value,
            instance_id=record["instance_id"],
            previous_instance_id=previous_instance_id,
        )

        # track primary keys and error if there is a duplicate
        primary_keys = (milestone_schema.interval, milestone_schema.instance_id)

        if primary_keys in milestone_primary_keys:
            logger.info(milestone_schema)
            raise ValueError(f"Duplicate milestone record: {primary_keys}")

        milestone_primary_keys.append(primary_keys)

        milestone_records.append(milestone_schema)

    return milestone_records


_DEFAULT_PERIODS = [
    MilestonePeriod.interval,
    MilestonePeriod.day,
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
]

_DEFAULT_NETWORKS = [NetworkNEM]


async def run_milestone_analysis(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> None:
    """
    Run milestone analysis across all grouping configurations.

    Args:
        start_date: Optional start date to limit analysis
        end_date: Optional end date to limit analysis
    """
    client = get_clickhouse_client()

    # Iterate through all periods and grouping configurations
    for metric in _DEFAULT_METRICS:
        for network in _DEFAULT_NETWORKS:
            for period in _DEFAULT_PERIODS:
                milestone_records: list[MilestoneRecordSchema] = []

                for grouping in GROUPING_CONFIGS:
                    if metric in [MilestoneType.power, MilestoneType.energy, MilestoneType.emissions]:
                        if period == MilestonePeriod.interval and metric not in [MilestoneType.power]:
                            continue

                        if period != MilestonePeriod.interval and metric == MilestoneType.power:
                            continue

                        records = analyze_generation_records(
                            client=client,
                            network=network,
                            milestone_type=metric,
                            period=period,
                            grouping=grouping,
                            start_date=start_date,
                            end_date=end_date,
                        )

                        milestone_records.extend(_analyzed_record_to_milestone_schema(records, network, period, metric, grouping))

                    elif metric in [MilestoneType.price, MilestoneType.demand]:
                        # Skip fueltech-related groupings for market summary records
                        if grouping.name in [
                            "fueltech",
                            "region_fueltech",
                            "renewable",
                            "region_renewable",
                        ]:
                            continue

                        records = analyze_market_summary_records(
                            client=client,
                            network=network,
                            milestone_type=metric,
                            period=period,
                            grouping=grouping,
                            start_date=start_date,
                            end_date=end_date,
                        )

                        milestone_records.extend(_analyzed_record_to_milestone_schema(records, network, period, metric, grouping))

                if milestone_records:
                    logger.info(
                        f"Found {len(milestone_records)} milestone records for {network.code} {metric.value} {period.value}"
                    )

                    await persist_milestones(milestone_records)

    logger.info("Milestone analysis complete")


async def run_milestone_analysis_backlog():
    """
    Runs in year chunks
    """
    end_date = get_last_completed_interval_for_network(NetworkNEM)
    start_date = NetworkNEM.data_first_seen
    # start_date = end_date - timedelta(days=90)

    await run_milestone_analysis(start_date=start_date, end_date=end_date)


if __name__ == "__main__":
    # Run test for last year of data
    import asyncio
    from datetime import datetime

    asyncio.run(run_milestone_analysis_backlog())
