"""
Bulk analysis of milestone records


To run the entire historic analysis and find new records for all record types, we run this optimised
bulk analyiser which takes a parquet file and runs the analysis for all record types and periods.

The live engine which runs per interval is located at opennem.recordreactor.engine
"""

import logging
from dataclasses import dataclass
from textwrap import dedent

import duckdb
import polars as pl

from opennem.recordreactor.persistence import persist_milestones
from opennem.recordreactor.schema import (
    MilestoneAggregate,
    MilestoneFueltechGrouping,
    MilestonePeriod,
    MilestoneRecordSchema,
    MilestoneType,
)
from opennem.recordreactor.unit import get_milestone_unit
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM

logger = logging.getLogger("opennem.recordreactor.bulk")


def get_time_bucket_sql(period: MilestonePeriod) -> str:
    """Generate SQL for different time bucket periods."""
    if period == MilestonePeriod.interval:
        return "interval"
    elif period == MilestonePeriod.day:
        return "DATE_TRUNC('day', interval)"
    elif period == MilestonePeriod.month:
        return "DATE_TRUNC('month', interval)"
    elif period == MilestonePeriod.quarter:
        return "DATE_TRUNC('quarter', interval)"
    elif period == MilestonePeriod.year:
        return "DATE_TRUNC('year', interval)"
    elif period == MilestonePeriod.financial_year:
        return """
            CASE
                WHEN EXTRACT(MONTH FROM interval) >= 7
                THEN DATE_TRUNC('year', interval) + INTERVAL '1 year'
                ELSE DATE_TRUNC('year', interval)
            END
        """
    else:
        raise ValueError(f"Unsupported period: {period}")


@dataclass
class GroupingConfig:
    """Configuration for how to group generation records"""

    name: str
    group_by_fields: list[str] | None


# Define all possible grouping configurations
GROUPING_CONFIGS = [
    GroupingConfig(name="network", group_by_fields=None),
    GroupingConfig(name="region", group_by_fields=["network_region"]),
    GroupingConfig(name="fueltech", group_by_fields=["fueltech_group_code"]),
    GroupingConfig(name="renewable", group_by_fields=["renewable"]),
    GroupingConfig(name="region_fueltech", group_by_fields=["network_region", "fueltech_group_code"]),
    GroupingConfig(name="region_renewable", group_by_fields=["network_region", "renewable"]),
]


def analyze_generation_records(
    parquet_path: str, network: NetworkSchema, period: MilestonePeriod, milestone_type: MilestoneType, grouping: GroupingConfig
) -> pl.DataFrame:
    """
    Analyze historical generation records using configurable grouping options.
    """
    con = duckdb.connect("data/opennem.duckdb")

    time_bucket_sql = get_time_bucket_sql(period)

    # Build the GROUP BY clause from the configuration
    group_by_fields = [time_bucket_sql]

    if grouping.group_by_fields:
        group_by_fields.extend(grouping.group_by_fields)

    group_by_clause = ",\n        ".join(group_by_fields)

    # Build partition fields for window functions - join with commas for SQL syntax
    partition_fields = []

    if grouping.group_by_fields:
        partition_fields = [f for f in grouping.group_by_fields if f != "network_id"]

    partition_clause = ", ".join(partition_fields) if partition_fields else "1"

    # Handle group by fields in SELECT statements
    group_by_select = f", {', '.join(grouping.group_by_fields)}" if grouping.group_by_fields else ""

    base_query = f"""
    WITH regional_generation AS (
      SELECT
        {time_bucket_sql} as interval{group_by_select},
        SUM(generated) as total_generation
      FROM read_parquet(?)
      WHERE
        network_id in (
            '{network.code.upper()}',
            {', '.join([
                f"'{i.code.upper()}'"
                for i in network.subnetworks
                if network.subnetworks is not None
            ])}
        ) and
        network_region in ({', '.join([f"'{i}'" for i in network.regions])})
      GROUP BY
        {group_by_clause}
    ),

    running_maxes AS (
      SELECT
        {time_bucket_sql} as interval{group_by_select},
        total_generation,
        MAX(total_generation) OVER (
          PARTITION BY {partition_clause}
          ORDER BY {time_bucket_sql}
          ROWS UNBOUNDED PRECEDING
        ) as running_max,
        uuid() as instance_id
      FROM regional_generation
      WHERE total_generation > 0
    ),

    max_records AS (
      SELECT
        {time_bucket_sql} as interval{group_by_select},
        total_generation,
        running_max,
        instance_id,
        LAG(running_max) OVER (
          PARTITION BY {partition_clause}
          ORDER BY {time_bucket_sql}
        ) as prev_max,
        LAG(instance_id) OVER (
          PARTITION BY {partition_clause}
          ORDER BY {time_bucket_sql}
        ) as prev_instance_id
      FROM running_maxes
    ),

    running_mins AS (
      SELECT
        {time_bucket_sql} as interval{group_by_select},
        total_generation,
        MIN(CASE WHEN total_generation > 0 THEN total_generation END) OVER (
          PARTITION BY {partition_clause}
          ORDER BY {time_bucket_sql}
          ROWS UNBOUNDED PRECEDING
        ) as running_min,
        uuid() as instance_id
      FROM regional_generation
      WHERE total_generation > 0
    ),

    min_records AS (
      SELECT
        {time_bucket_sql} as interval{group_by_select},
        total_generation,
        running_min,
        instance_id,
        LAG(running_min) OVER (
          PARTITION BY {partition_clause}
          ORDER BY {time_bucket_sql}
        ) as prev_min,
        LAG(instance_id) OVER (
          PARTITION BY {partition_clause}
          ORDER BY {time_bucket_sql}
        ) as prev_instance_id
      FROM running_mins
    )

    (SELECT
      {time_bucket_sql} as interval{group_by_select},
      total_generation,
      CASE
        WHEN prev_max IS NULL THEN 0
        ELSE ((total_generation - prev_max) / prev_max * 100)
      END as pct_change,
      'high' as record_type,
      '{milestone_type.value}' as metric,
      '{period.value}' as period,
      instance_id,
      prev_instance_id
    FROM max_records
    WHERE
      total_generation = running_max
      AND (prev_max IS NULL OR total_generation > prev_max))

    UNION ALL

    (SELECT
      {time_bucket_sql} as interval{group_by_select},
      total_generation,
      CASE
        WHEN prev_min IS NULL THEN 0
        ELSE ((total_generation - prev_min) / prev_min * 100)
      END as pct_change,
      'low' as record_type,
      '{milestone_type.value}' as metric,
      '{period.value}' as period,
      instance_id,
      prev_instance_id
    FROM min_records
    WHERE
      total_generation = running_min
      AND (prev_min IS NULL OR total_generation < prev_min))

    ORDER BY interval, metric;
    """

    try:
        df = con.execute(base_query, [parquet_path]).pl()
    except Exception as e:
        print(dedent(base_query))
        logger.error(f"Error during bulk milestone insertion: {str(e)}")
        raise
    finally:
        con.close()

    return df


_DEFAULT_PERIODS = [
    MilestonePeriod.interval,
    MilestonePeriod.day,
    MilestonePeriod.month,
    # MilestonePeriod.quarter,
    MilestonePeriod.year,
    # MilestonePeriod.financial_year,
]


def _analyzed_record_to_milestone_schema(
    df: pl.DataFrame, network: NetworkSchema, period: MilestonePeriod, milestone_type: MilestoneType, grouping: GroupingConfig
) -> list[MilestoneRecordSchema]:
    """
    Convert an analyzed record dataframe to a list of milestone record schemas using vectorized operations.

    Args:
        df: Polars DataFrame containing the analyzed records
        milestone_type: Type of milestone being processed
        grouping: GroupingConfig specifying how records were grouped

    Returns:
        list[MilestoneRecordSchema]: List of milestone records converted to schema objects
    """
    unit = get_milestone_unit(milestone_type)

    # Get lists of values, handling optional fields based on grouping
    intervals = df["interval"].to_list()
    values = df["total_generation"].to_list()
    record_types = df["record_type"].to_list()
    instance_ids = df["instance_id"].to_list()
    prev_instance_ids = df["prev_instance_id"].to_list()

    # Handle optional fields based on grouping configuration
    network_regions = (
        df["network_region"].to_list()
        if grouping.group_by_fields and "network_region" in grouping.group_by_fields
        else [None] * len(intervals)
    )

    # Handle fueltech based on grouping type
    if grouping.group_by_fields and "renewable" in grouping.group_by_fields:
        renewable_values = df["renewable"].to_list()
        fueltechs = ["renewables" if is_renewable else "fossils" for is_renewable in renewable_values]
    elif grouping.group_by_fields and "fueltech_group_code" in grouping.group_by_fields:
        fueltechs = df["fueltech_group_code"].to_list()
    else:
        fueltechs = [None] * len(intervals)

    return [
        MilestoneRecordSchema(
            interval=interval,
            aggregate=MilestoneAggregate(record_type),
            metric=milestone_type,
            period=period,
            network=network,
            unit=unit,
            network_region=network_region,
            fueltech=MilestoneFueltechGrouping(fueltech) if fueltech else None,
            value=value,
            instance_id=instance_id,
            previous_instance_id=prev_instance_id,
        )
        for (
            interval,
            network_region,
            fueltech,
            value,
            record_type,
            instance_id,
            prev_instance_id,
        ) in zip(
            intervals,
            network_regions,
            fueltechs,
            values,
            record_types,
            instance_ids,
            prev_instance_ids,
            strict=True,
        )
    ]


async def run_milestone_analysis(parquet_path: str) -> None:
    """
    Run milestone analysis for a given parquet file across all grouping configurations.
    """
    df = pl.read_parquet(parquet_path)
    print(df.shape)
    print(df.columns)
    print(df.head())

    milestone_records: list[MilestoneRecordSchema] = []

    # Iterate through all periods and grouping configurations
    for network in [NetworkNEM, NetworkWEM]:
        for period in _DEFAULT_PERIODS:
            for grouping in GROUPING_CONFIGS:
                logger.info(f"Analyzing {network.code} {period.value} records with grouping: {grouping.name}")

                records_df = analyze_generation_records(
                    parquet_path=parquet_path,
                    network=network,
                    period=period,
                    milestone_type=MilestoneType.power,
                    grouping=grouping,
                )

                milestone_records.extend(
                    _analyzed_record_to_milestone_schema(records_df, network, period, MilestoneType.power, grouping)
                )

    logger.info(f"Found {len(milestone_records)} milestone records")

    # Persist in chunks to avoid memory issues
    await persist_milestones(milestone_records)


if __name__ == "__main__":
    # Path to your parquet file
    parquet_path = "data/fueltech_interval_all.parquet"
    parquet_path = "data/1y_fueltech_interval_data.parquet"

    # Run analysis
    import asyncio

    asyncio.run(run_milestone_analysis(parquet_path))
