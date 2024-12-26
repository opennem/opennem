"""
Bulk analysis of milestone records


To run the entire historic analysis and find new records for all record types, we run this optimised
bulk analyiser which takes a parquet file and runs the analysis for all record types and periods.

The live engine which runs per interval is located at opennem.recordreactor.engine
"""

import logging

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
from opennem.schema.network import NetworkNEM, NetworkWEM

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


def analyze_generation_records(parquet_path: str, period: MilestonePeriod, milestone_type: MilestoneType) -> pl.DataFrame:
    """
    Analyze historical generation records by region and fuel type using DuckDB.
    Returns both maximum and minimum records with instance IDs linking to previous records.

    Args:
        parquet_path: Path to the parquet file containing generation data
        period: The time period to analyze (interval, day, month, etc)
        milestone_type: Type of milestone being analyzed

    Returns:
        pl.DataFrame: DataFrame containing records with instance_id and previous_instance_id fields
    """
    # Connect to DuckDB
    con = duckdb.connect("data/opennem.duckdb")

    time_bucket_sql = get_time_bucket_sql(period)

    # The query - now with instance_id tracking
    query = f"""
    WITH regional_generation AS (
      SELECT
        {time_bucket_sql} as interval,
        network_id,
        network_region,
        fueltech_group_code,
        SUM(generated) as total_generation
      FROM read_parquet(?)
      GROUP BY
        interval,
        network_id,
        network_region,
        fueltech_group_code
    ),

    -- Calculate running maximums with instance IDs
    running_maxes AS (
      SELECT
        interval,
        network_id,
        network_region,
        fueltech_group_code,
        total_generation,
        MAX(total_generation) OVER (
          PARTITION BY network_region, fueltech_group_code
          ORDER BY interval
          ROWS UNBOUNDED PRECEDING
        ) as running_max,
        uuid() as instance_id
      FROM regional_generation
      WHERE total_generation > 0
    ),

    -- Get maximum records with previous instance tracking
    max_records AS (
      SELECT
        interval,
        network_id,
        network_region,
        fueltech_group_code,
        total_generation,
        running_max,
        instance_id,
        LAG(running_max) OVER (
          PARTITION BY network_region, fueltech_group_code
          ORDER BY interval
        ) as prev_max,
        LAG(instance_id) OVER (
          PARTITION BY network_region, fueltech_group_code
          ORDER BY interval
        ) as prev_instance_id
      FROM running_maxes
    ),

    -- Calculate running minimums with instance IDs
    running_mins AS (
      SELECT
        interval,
        network_id,
        network_region,
        fueltech_group_code,
        total_generation,
        MIN(CASE WHEN total_generation > 0 THEN total_generation END) OVER (
          PARTITION BY network_region, fueltech_group_code
          ORDER BY interval
          ROWS UNBOUNDED PRECEDING
        ) as running_min,
        uuid() as instance_id
      FROM regional_generation
      WHERE total_generation > 0
    ),

    -- Get minimum records with previous instance tracking
    min_records AS (
      SELECT
        interval,
        network_id,
        network_region,
        fueltech_group_code,
        total_generation,
        running_min,
        instance_id,
        LAG(running_min) OVER (
          PARTITION BY network_region, fueltech_group_code
          ORDER BY interval
        ) as prev_min,
        LAG(instance_id) OVER (
          PARTITION BY network_region, fueltech_group_code
          ORDER BY interval
        ) as prev_instance_id
      FROM running_mins
    )

    -- Combine maximum and minimum records
    (SELECT
      interval,
      network_id,
      network_region,
      fueltech_group_code,
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
      interval,
      network_id,
      network_region,
      fueltech_group_code,
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

    ORDER BY interval, metric, network_id, network_region, fueltech_group_code;
    """

    # Execute query and convert to polars DataFrame
    df = con.execute(query, [parquet_path]).pl()

    # Close connection
    con.close()

    return df


_DEFAULT_PERIODS = [
    MilestonePeriod.interval,
    # MilestonePeriod.day,
    # MilestonePeriod.month,
    # MilestonePeriod.quarter,
    # MilestonePeriod.year,
    # MilestonePeriod.financial_year,
]


def _analyzed_record_to_milestone_schema(df: pl.DataFrame, milestone_type: MilestoneType) -> list[MilestoneRecordSchema]:
    """
    Convert an analyzed record dataframe to a list of milestone record schemas using vectorized operations.

    Args:
        df: Polars DataFrame containing the analyzed records
        milestone_type: Type of milestone being processed

    Returns:
        list[MilestoneRecordSchema]: List of milestone records converted to schema objects
    """
    unit = get_milestone_unit(milestone_type)

    return [
        MilestoneRecordSchema(
            interval=interval,
            aggregate=MilestoneAggregate(record_type),
            metric=milestone_type,
            period=MilestonePeriod(period),
            network=NetworkNEM if network_id.upper() in ["NEM", "AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL"] else NetworkWEM,
            unit=unit,
            network_region=network_region,
            fueltech=MilestoneFueltechGrouping(fueltech_code),
            value=value,
            instance_id=instance_id,
            previous_instance_id=prev_instance_id,
        )
        for (
            interval,
            network_region,
            fueltech_code,
            value,
            record_type,
            period,
            network_id,
            instance_id,
            prev_instance_id,
        ) in zip(
            df["interval"].to_list(),
            df["network_region"].to_list(),
            df["fueltech_group_code"].to_list(),
            df["total_generation"].to_list(),
            df["record_type"].to_list(),
            df["period"].to_list(),
            df["network_id"].to_list(),
            df["instance_id"].to_list(),
            df["prev_instance_id"].to_list(),
            strict=False,
        )
    ]


async def run_milestone_analysis(parquet_path: str) -> None:
    """
    Run milestone analysis for a given parquet file.
    """

    # preview the shape of the data, show all the fields and the first 5 rows
    df = pl.read_parquet(parquet_path)
    print(df.shape)
    print(df.columns)
    print(df.head())

    milestone_records: list[MilestoneRecordSchema] = []

    for period in _DEFAULT_PERIODS:
        records_df = analyze_generation_records(parquet_path=parquet_path, period=period, milestone_type=MilestoneType.power)

        milestone_records.extend(_analyzed_record_to_milestone_schema(records_df, MilestoneType.power))

    logger.info(f"Found {len(milestone_records)} milestone records")

    await persist_milestones(milestone_records)


if __name__ == "__main__":
    # Path to your parquet file
    parquet_path = "data/fueltech_interval_all.parquet"
    parquet_path = "data/1y_fueltech_interval_data.parquet"

    # Run analysis
    import asyncio

    asyncio.run(run_milestone_analysis(parquet_path))
