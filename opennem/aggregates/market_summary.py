"""
Market Summary aggregation module.

This module handles the aggregation of market summary data from PostgreSQL to ClickHouse.
It calculates energy values from demand readings and stores them in ClickHouse for efficient querying.
"""

import logging
from collections.abc import Sequence
from datetime import datetime, timedelta

import polars as pl
from clickhouse_driver.client import Client
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import get_write_session
from opennem.db.clickhouse import (
    create_table_if_not_exists,
    get_clickhouse_client,
    table_exists,
)
from opennem.db.clickhouse_schema import (
    MARKET_SUMMARY_TABLE_SCHEMA,
)
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.aggregates.market_summary")


async def _get_market_summary_data(
    session: AsyncSession, start_time: datetime, end_time: datetime
) -> list[tuple[datetime, str, str, float | None, float | None, float | None]]:
    """
    Get market summary data from PostgreSQL for a given time range.

    Args:
        session: Database session
        start_time: Start time for data range
        end_time: End date for data range

    Returns:
        List of tuples containing (interval, network_id, network_region, price, demand, demand_total)
    """
    # Strip timezone info
    start_time_naive = start_time.replace(tzinfo=None)
    end_time_naive = end_time.replace(tzinfo=None)

    query = text("""
    WITH ranked_data AS (
        SELECT
            interval,
            network_id,
            network_region,
            CAST(price AS double precision) as price,
            CAST(demand AS double precision) as demand,
            CAST(demand_total AS double precision) as demand_total,
            LAG(CAST(demand AS double precision)) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_demand,
            LAG(CAST(demand_total AS double precision)) OVER (
                PARTITION BY network_id, network_region
                ORDER BY interval
            ) as prev_demand_total
        FROM balancing_summary
        WHERE interval BETWEEN :start_time AND :end_time
        AND is_forecast = false
        ORDER BY interval
    )
    SELECT
        interval,
        network_id,
        network_region,
        price,
        demand,
        demand_total,
        prev_demand,
        prev_demand_total
    FROM ranked_data
    WHERE prev_demand IS NOT NULL
    """)

    result = await session.execute(query, {"start_time": start_time_naive, "end_time": end_time_naive})
    return result.fetchall()


def _prepare_market_summary_data(
    records: Sequence[tuple[datetime, str, str, float | None, float | None, float | None, float | None, float | None]],
) -> list[tuple[datetime, str, str, float | None, float | None, float | None, float | None, float | None]]:
    """
    Prepare market summary data for ClickHouse by calculating energy values.

    Args:
        records: Raw records from PostgreSQL
        network_intervals: Dictionary mapping network_id to interval size in minutes

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
            "price": pl.Float64,
            "demand": pl.Float64,
            "demand_total": pl.Float64,
            "prev_demand": pl.Float64,
            "prev_demand_total": pl.Float64,
        },
    )

    network_intervals = {
        "NEM": 5,
        "WEM": 30,
    }

    # Create intervals_per_hour mapping
    intervals_map = {network: 60 / interval for network, interval in network_intervals.items()}
    default_intervals = 60 / 5  # Default to 5-minute intervals

    # Calculate energy values using vectorized operations
    df = df.with_columns(
        [
            (
                (
                    (pl.col("demand") + pl.col("prev_demand"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                ).round(4)
            ).alias("demand_energy"),
            (
                (
                    (pl.col("demand_total") + pl.col("prev_demand_total"))
                    / 2
                    / pl.when(pl.col("network_id").is_in(list(intervals_map.keys())))
                    .then(
                        pl.col("network_id").map_elements(
                            lambda x: intervals_map.get(x, default_intervals), return_dtype=pl.Float64
                        )
                    )
                    .otherwise(default_intervals)
                ).round(4)
            ).alias("demand_total_energy"),
        ]
    )

    # Calculate market values
    df = df.with_columns(
        [
            (pl.col("demand_energy") * pl.col("price")).round(4).alias("demand_market_value"),
            (pl.col("demand_total_energy") * pl.col("price")).round(4).alias("demand_total_market_value"),
        ]
    )

    # Select and order columns for ClickHouse insertion
    result_df = df.select(
        [
            "interval",
            "network_id",
            "network_region",
            "price",
            "demand",
            "demand_total",
            "demand_energy",
            "demand_total_energy",
            "demand_market_value",
            "demand_total_market_value",
        ]
    )

    # Convert back to list of tuples for ClickHouse insertion
    return result_df.rows()


def _ensure_clickhouse_schema(client: Client) -> None:
    """
    Ensure ClickHouse schema exists by creating tables and views if needed.

    Args:
        client: ClickHouse client
    """
    if not table_exists(client, "market_summary"):
        create_table_if_not_exists(client, "market_summary", MARKET_SUMMARY_TABLE_SCHEMA)
        # client.execute(MARKET_SUMMARY_DAILY_MV)
        # client.execute(MARKET_SUMMARY_MONTHLY_MV)


def _refresh_clickhouse_schema() -> None:
    """
    Refresh ClickHouse schema by dropping and recreating tables and views.

    """
    client = get_clickhouse_client()
    client.execute("DROP TABLE IF EXISTS market_summary")
    client.execute("DROP VIEW IF EXISTS market_summary_daily_mv")
    client.execute("DROP VIEW IF EXISTS market_summary_monthly_mv")

    _ensure_clickhouse_schema(client)


async def process_market_summary_backlog(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    chunk_size: timedelta = timedelta(days=7),
) -> None:
    """
    Process historical market summary data in chunks.

    Args:
        session: Database session
        start_date: Start date for processing
        end_date: End date for processing
        network_intervals: Dictionary mapping network_id to interval size
        chunk_size: Size of each processing chunk
    """
    current_start = start_date
    client = get_clickhouse_client()
    _ensure_clickhouse_schema(client)

    while current_start < end_date:
        chunk_end = min(current_start + chunk_size, end_date)

        # Get and process data for this chunk
        records = await _get_market_summary_data(session, current_start, chunk_end)
        if records:
            prepared_data = _prepare_market_summary_data(records)

            # Batch insert into ClickHouse
            client.execute(
                """
                INSERT INTO market_summary
                (interval, network_id, network_region, price, demand, demand_total,
                 demand_energy, demand_total_energy, demand_market_value, demand_total_market_value)
                VALUES
                """,
                prepared_data,
            )

            logger.info(f"Processed {len(prepared_data)} records from {current_start} to {chunk_end}")

        current_start = chunk_end


async def run_market_summary_aggregate_to_now() -> int:
    """ """
    client = get_clickhouse_client()

    # get the max interval from market_summary
    result = client.execute("SELECT MAX(interval) FROM market_summary")
    max_interval = result[0][0]

    date_from = max_interval + timedelta(minutes=5)
    date_to = get_last_completed_interval_for_network(network=NetworkNEM)

    if date_from > date_to:
        logger.info("No new data to process")
        return 0

    # run market summary from max_interval to now
    async with get_write_session() as session:
        records = await _get_market_summary_data(session, date_from, date_to)
        prepared_data = _prepare_market_summary_data(records)

    client.execute(
        """
        INSERT INTO market_summary
        (interval, network_id, network_region, price, demand, demand_total,
         demand_energy, demand_total_energy, demand_market_value, demand_total_market_value)
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {date_from} to {date_to}")

    return len(prepared_data)


async def run_market_summary_aggregate_for_last_intervals(num_intervals: int) -> int:
    """
    Run the market summary aggregation for the last num_intervals
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = end_date - timedelta(minutes=num_intervals * 5)

    async with get_write_session() as session:
        records = await _get_market_summary_data(session, start_date, end_date)
        prepared_data = _prepare_market_summary_data(records)

    client = get_clickhouse_client()

    client.execute(
        """
        INSERT INTO market_summary
        (interval, network_id, network_region, price, demand, demand_total,
         demand_energy, demand_total_energy, demand_market_value, demand_total_market_value)
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {start_date} to {end_date}")

    return len(prepared_data)


async def run_market_summary_backlog() -> None:
    """
    Run the market summary aggregation for the history of the market.
    """

    # Calculate date range for the past week
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = NetworkNEM.data_first_seen.replace(tzinfo=None)

    # Ensure ClickHouse schema exists
    client = get_clickhouse_client()
    _ensure_clickhouse_schema(client)

    # Process the data
    async with get_write_session() as session:
        await process_market_summary_backlog(
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
        FROM market_summary
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


if __name__ == "__main__":
    # Run the test
    async def main():
        _refresh_clickhouse_schema()
        await run_market_summary_backlog()
        # await run_market_summary_aggregate_for_last_intervals(num_intervals=12 * 24 * 1)
        # await run_market_summary_aggregate_for_last_intervals(num_intervals=12 * 24 * 1)

    import asyncio

    asyncio.run(run_market_summary_aggregate_to_now())