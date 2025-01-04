"""
Unit Intervals aggregation module.

This module handles the aggregation of unit interval data from PostgreSQL to ClickHouse.
It calculates energy values, emissions, and market values for each unit and stores them in ClickHouse.
"""

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta

import polars as pl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import get_write_session
from opennem.db.clickhouse import (
    create_table_if_not_exists,
    get_clickhouse_client,
    table_exists,
)
from opennem.db.clickhouse_schema import UNIT_INTERVALS_DAILY_MV, UNIT_INTERVALS_MONTHLY_MV, UNIT_INTERVALS_TABLE_SCHEMA
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.aggregates.unit_intervals")


async def _get_unit_interval_data(session: AsyncSession, start_time: datetime, end_time: datetime) -> list[tuple]:
    """
    Get unit interval data from PostgreSQL for a given time range.

    Args:
        session: Database session
        start_time: Start time for data range
        end_time: End date for data range

    Returns:
        List of tuples containing unit interval data
    """
    # Strip timezone info
    start_time_naive = start_time.replace(tzinfo=None)
    end_time_naive = end_time.replace(tzinfo=None)

    query = text("""
    WITH filled_balancing_summary AS (
        SELECT
            time_bucket_gapfill('5 minutes', bs.interval) as interval,
            bs.network_id,
            bs.network_region,
            locf(
                avg(bs.demand)
            ) AS demand,
            locf(
                avg(bs.demand_total)
            ) as demand_total,
            locf(
                avg(bs.price)
            ) AS price
        FROM balancing_summary bs
        WHERE
            bs.interval >= :start_time
            AND bs.interval <= :end_time
        GROUP BY 1, 2, 3
    )
    SELECT
        time_bucket('5 minutes', fs.interval) as interval,
        fs.network_id,
        f.network_region,
        f.code as facility_code,
        u.code as unit_code,
        u.status_id,
        u.fueltech_id,
        ftg.code as fueltech_group_id,
        ftg.renewable as renewable,
        round(sum(fs.generated), 4) as generated,
        round(sum(fs.energy), 4) as energy,
        CASE
            WHEN sum(fs.energy) > 0 THEN coalesce(round(sum(u.emissions_factor_co2 * fs.energy), 4), 0)
            ELSE 0
        END as emissions,
        CASE
            WHEN sum(fs.energy) > 0 THEN coalesce(round(sum(u.emissions_factor_co2 * fs.energy) / sum(fs.energy), 4), 0)
            ELSE 0
        END as emission_factor,
        CASE
            WHEN sum(fs.energy) > 0 THEN round(sum(fs.energy) * max(bs.price), 4)
            ELSE 0
        END as market_value
    FROM
        facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        JOIN fueltech ft ON ft.code = u.fueltech_id
        JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
        LEFT JOIN filled_balancing_summary bs ON
            bs.interval = fs.interval
            AND bs.network_region = f.network_region
    WHERE
        fs.is_forecast IS FALSE
        AND u.fueltech_id IS NOT NULL
        AND u.fueltech_id NOT IN ('imports', 'exports', 'interconnector', 'battery')
        AND fs.interval >= :start_time
        AND fs.interval < :end_time
    GROUP BY 1,2,3,4,5,6,7,8,9
    ORDER BY 1,2,3,4,5
    """)

    result = await session.execute(query, {"start_time": start_time_naive, "end_time": end_time_naive})
    return result.fetchall()


def _prepare_unit_interval_data(records: Sequence[tuple]) -> list[tuple]:
    """
    Prepare unit interval data for ClickHouse by converting to the correct format.

    Args:
        records: Raw records from PostgreSQL

    Returns:
        List of tuples ready for ClickHouse insertion
    """
    if not records:
        return []

    # Convert records to polars DataFrame
    df = pl.DataFrame(
        records,
        schema={
            "interval": pl.Datetime,
            "network_id": pl.String,
            "network_region": pl.String,
            "facility_code": pl.String,
            "unit_code": pl.String,
            "status_id": pl.String,
            "fueltech_id": pl.String,
            "fueltech_group_id": pl.String,
            "renewable": pl.Boolean,
            "generated": pl.Float64,
            "energy": pl.Float64,
            "emissions": pl.Float64,
            "emission_factor": pl.Float64,
            "market_value": pl.Float64,
        },
    )

    # Round numeric values to 4 decimal places
    numeric_cols = ["generated", "energy", "emissions", "emission_factor", "market_value"]
    df = df.with_columns([pl.col(col).round(4) for col in numeric_cols])

    # Convert back to list of tuples for ClickHouse insertion
    return df.rows()


def _ensure_clickhouse_schema() -> None:
    """
    Ensure ClickHouse schema exists by creating tables and views if needed.

    Args:
        client: ClickHouse client
    """
    client = get_clickhouse_client()
    if not table_exists(client, "unit_intervals"):
        create_table_if_not_exists(client, "unit_intervals", UNIT_INTERVALS_TABLE_SCHEMA)
        logger.info("Created unit_intervals")

    if not table_exists(client, "unit_intervals_daily_mv"):
        client.execute(UNIT_INTERVALS_DAILY_MV)
        logger.info("Created unit_intervals_daily_mv")

    if not table_exists(client, "unit_intervals_monthly_mv"):
        client.execute(UNIT_INTERVALS_MONTHLY_MV)
        logger.info("Created unit_intervals_monthly_mv")


def _refresh_clickhouse_schema() -> None:
    """
    Refresh ClickHouse schema by dropping and recreating tables and views.
    """

    # insert a prompt here for the user to confirm
    print("This will drop and recreate all unit_intervals tables and views. Are you sure you want to continue? (y/n)")
    if input().lower() != "y":
        logger.info("User cancelled")
        return

    client = get_clickhouse_client()
    client.execute("DROP TABLE IF EXISTS unit_intervals_monthly_mv")
    client.execute("DROP TABLE IF EXISTS unit_intervals_daily_mv")
    client.execute("DROP TABLE IF EXISTS unit_intervals")
    _ensure_clickhouse_schema(client)


async def process_unit_intervals_backlog(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    chunk_size: timedelta = timedelta(days=7),
) -> None:
    """
    Process historical unit interval data in chunks.

    Args:
        session: Database session
        start_date: Start date for processing
        end_date: End date for processing
        chunk_size: Size of each processing chunk
    """
    current_start = start_date
    client = get_clickhouse_client()
    _ensure_clickhouse_schema(client)

    while current_start < end_date:
        chunk_end = min(current_start + chunk_size, end_date)

        # Get and process data for this chunk
        records = await _get_unit_interval_data(session, current_start, chunk_end)
        if records:
            prepared_data = _prepare_unit_interval_data(records)

            # Batch insert into ClickHouse
            client.execute(
                """
                INSERT INTO unit_intervals
                (interval, network_id, network_region, facility_code, unit_code,
                 status_id, fueltech_id, fueltech_group_id, renewable,
                 generated, energy, emissions, emission_factor, market_value)
                VALUES
                """,
                prepared_data,
            )

            logger.info(f"Processed {len(prepared_data)} records from {current_start} to {chunk_end}")

        current_start = chunk_end


async def run_unit_intervals_aggregate_to_now() -> int:
    """
    Run the unit intervals aggregation from the last processed interval to now.

    Returns:
        int: Number of records processed
    """
    client = get_clickhouse_client()

    # get the max interval from unit_intervals
    result = client.execute("SELECT MAX(interval) FROM unit_intervals")
    max_interval = result[0][0]

    date_from = max_interval + timedelta(minutes=5)
    date_to = get_last_completed_interval_for_network(network=NetworkNEM)

    if date_from > date_to:
        logger.info("No new data to process")
        return 0

    # run unit intervals from max_interval to now
    async with get_write_session() as session:
        records = await _get_unit_interval_data(session, date_from, date_to)
        prepared_data = _prepare_unit_interval_data(records)

    client.execute(
        """
        INSERT INTO unit_intervals
        (interval, network_id, network_region, facility_code, unit_code,
         status_id, fueltech_id, fueltech_group_id, renewable,
         generated, energy, emissions, emission_factor, market_value)
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {date_from} to {date_to}")

    return len(prepared_data)


async def run_unit_intervals_aggregate_for_last_intervals(num_intervals: int) -> int:
    """
    Run the unit intervals aggregation for the last num_intervals.

    Args:
        num_intervals: Number of 5-minute intervals to process

    Returns:
        int: Number of records processed
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = end_date - timedelta(minutes=num_intervals * 5)

    async with get_write_session() as session:
        records = await _get_unit_interval_data(session, start_date, end_date)
        prepared_data = _prepare_unit_interval_data(records)

    client = get_clickhouse_client()

    client.execute(
        """
        INSERT INTO unit_intervals
        (interval, network_id, network_region, facility_code, unit_code,
         status_id, fueltech_id, fueltech_group_id, renewable,
         generated, energy, emissions, emission_factor, market_value)
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {start_date} to {end_date}")

    return len(prepared_data)


async def run_unit_intervals_backlog() -> None:
    """
    Run the unit intervals aggregation for the history of the market.
    """
    # Calculate date range
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = NetworkNEM.data_first_seen.replace(tzinfo=None)

    # Ensure ClickHouse schema exists
    client = get_clickhouse_client()

    # Process the data
    async with get_write_session() as session:
        await process_unit_intervals_backlog(
            session=session,
            start_date=start_date,
            end_date=end_date,
            chunk_size=timedelta(days=30),
        )

    # Verify the data was inserted
    result = client.execute(
        """
        SELECT
            network_id,
            network_region,
            count(*) as record_count,
            min(interval) as first_interval,
            max(interval) as last_interval
        FROM unit_intervals
        WHERE interval BETWEEN %(start)s AND %(end)s
        GROUP BY network_id, network_region
        """,
        {"start": start_date, "end": end_date},
    )

    # Log the results
    logger.info("Processing complete. Summary of inserted data:")
    for network_id, region, count, first, last in result:
        logger.info(
            f"Network: {network_id}, Region: {region}, Records: {count}, " f"Period: {first.isoformat()} to {last.isoformat()}"
        )


def backfill_materialized_views() -> None:
    """
    Backfill the materialized views from the base unit_intervals table.
    This should be run after bulk loading data into unit_intervals if the views are empty.
    """
    client = get_clickhouse_client()

    # Drop existing views
    logger.info("Dropping existing materialized views...")
    client.execute("DROP TABLE IF EXISTS unit_intervals_monthly_mv")
    client.execute("DROP TABLE IF EXISTS unit_intervals_daily_mv")

    # Recreate views
    logger.info("Recreating materialized views...")
    client.execute(UNIT_INTERVALS_DAILY_MV)
    client.execute(UNIT_INTERVALS_MONTHLY_MV)

    # Get date range from base table
    result = client.execute("""
        SELECT
            min(interval) as min_date,
            max(interval) as max_date
        FROM unit_intervals
    """)
    start_date, end_date = result[0]

    # Process month by month
    current_date = start_date.replace(day=1)
    while current_date <= end_date:
        next_month = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

        logger.info(f"Processing month {current_date.strftime('%Y-%m')}")

        # Backfill daily view for this month
        client.execute(
            """
            INSERT INTO unit_intervals_daily_mv
            SELECT
                toDate(interval) as date,
                network_id,
                network_region,
                facility_code,
                unit_code,
                fueltech_id,
                fueltech_group_id,
                any(renewable) as renewable,
                any(status_id) as status_id,
                avg(generated) as generated_avg,
                max(generated) as generated_max,
                min(generated) as generated_min,
                sum(energy) as energy_sum,
                sum(emissions) as emissions_sum,
                avg(emission_factor) as emission_factor_avg,
                sum(market_value) as market_value_sum,
                count() as count
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            GROUP BY
                date,
                network_id,
                network_region,
                facility_code,
                unit_code,
                fueltech_id,
                fueltech_group_id
        """,
            {"start": current_date, "end": next_month},
        )

        # Backfill monthly view for this month
        client.execute(
            """
            INSERT INTO unit_intervals_monthly_mv
            SELECT
                toStartOfMonth(interval) as month,
                network_id,
                network_region,
                facility_code,
                unit_code,
                fueltech_id,
                fueltech_group_id,
                any(renewable) as renewable,
                any(status_id) as status_id,
                avg(generated) as generated_avg,
                max(generated) as generated_max,
                min(generated) as generated_min,
                sum(energy) as energy_sum,
                sum(emissions) as emissions_sum,
                avg(emission_factor) as emission_factor_avg,
                sum(market_value) as market_value_sum,
                count() as count
            FROM unit_intervals
            WHERE interval >= %(start)s AND interval < %(end)s
            GROUP BY
                month,
                network_id,
                network_region,
                facility_code,
                unit_code,
                fueltech_id,
                fueltech_group_id
        """,
            {"start": current_date, "end": next_month},
        )

        current_date = next_month

    # Verify the backfill
    daily_count = client.execute("SELECT count() FROM unit_intervals_daily_mv")[0][0]
    monthly_count = client.execute("SELECT count() FROM unit_intervals_monthly_mv")[0][0]
    logger.info(f"Backfill complete. Daily records: {daily_count}, Monthly records: {monthly_count}")


if __name__ == "__main__":
    # Run the test
    async def main():
        _ensure_clickhouse_schema()
        # await run_unit_intervals_backlog()
        # await run_unit_intervals_aggregate_for_last_intervals(num_intervals=12 * 24 * 1)
        # Uncomment to backfill views:
        backfill_materialized_views()

    import asyncio

    asyncio.run(main())
