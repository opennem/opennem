"""
Unit Intervals aggregation module.

This module handles the aggregation of unit interval data from PostgreSQL to ClickHouse.
It calculates energy values, emissions, and market values for each unit and stores them in ClickHouse.
"""

import gc
import logging
from collections.abc import AsyncIterator, Sequence
from datetime import datetime, timedelta

import polars as pl
import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import get_write_session
from opennem.db.clickhouse import (
    create_table_if_not_exists,
    get_clickhouse_client,
    table_exists,
)
from opennem.db.clickhouse_materialized_views import (
    backfill_materialized_views,
    ensure_materialized_views_exist,
)
from opennem.db.clickhouse_schema import UNIT_INTERVALS_TABLE_SCHEMA, optimize_clickhouse_tables
from opennem.db.clickhouse_views import (
    FUELTECH_INTERVALS_DAILY_VIEW,
    FUELTECH_INTERVALS_VIEW,
    RENEWABLE_INTERVALS_DAILY_VIEW,
    RENEWABLE_INTERVALS_VIEW,
    UNIT_INTERVALS_DAILY_VIEW,
)
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.aggregates.unit_intervals")


def _monitor_memory_usage() -> float:
    """Monitor and log memory usage, trigger GC if needed.

    Returns:
        Memory usage in MB
    """
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.debug(f"Memory usage: {memory_mb:.1f} MB")

    if memory_mb > 6000:  # 6GB threshold
        logger.warning("High memory usage detected, forcing garbage collection")
        gc.collect()

    return memory_mb


# List of all materialized views to manage
_UNIT_INTERVALS_MATERIALIZED_VIEWS = [
    UNIT_INTERVALS_DAILY_VIEW,
    FUELTECH_INTERVALS_VIEW,
    FUELTECH_INTERVALS_DAILY_VIEW,
    RENEWABLE_INTERVALS_VIEW,
    RENEWABLE_INTERVALS_DAILY_VIEW,
]


async def _get_unit_interval_data(
    session: AsyncSession, start_time: datetime, end_time: datetime, network: NetworkSchema | None = None
) -> list[tuple]:
    """
    Get unit interval data from PostgreSQL for a given time range.

    Args:
        session: Database session
        start_time: Start time for data range
        end_time: End date for data range
        network: Optional network filter

    Returns:
        List of tuples containing unit interval data
    """
    # Strip timezone info
    start_time_naive = start_time.replace(tzinfo=None)
    end_time_naive = end_time.replace(tzinfo=None)

    network_where_clause = ""

    if network:
        network_where_clause = f"AND fs.network_id IN ('{"','".join(network.get_network_codes())}')"

    query = text(f"""
    WITH price_data AS (
        -- First get only the non-NULL price points
        SELECT
            interval,
            network_id,
            network_region,
            demand,
            demand_total,
            price
        FROM balancing_summary
        WHERE
            interval >= :start_time
            AND interval <= :end_time
            AND price IS NOT NULL
    ),
    filled_balancing_summary AS (
        -- Now gap-fill and carry forward the 30-minute prices to 5-minute intervals
        SELECT
            time_bucket_gapfill('5 minutes', pd.interval, :start_time, :end_time) as interval,
            pd.network_id,
            pd.network_region,
            locf(avg(pd.demand)) AS demand,
            locf(avg(pd.demand_total)) as demand_total,
            locf(avg(pd.price)) AS price
        FROM price_data pd
        GROUP BY 1, 2, 3
    ),
    filled_solar_data AS (
        SELECT
            time_bucket_gapfill('5 minutes', fs.interval) as interval,
            fs.network_id,
            f.network_region,
            f.code as facility_code,
            u.code as unit_code,
            u.status_id,
            u.fueltech_id,
            'solar' as fueltech_group_id,
            TRUE as renewable,
            locf(coalesce(round(sum(fs.generated), 4), 0)) as generated,
            locf(coalesce(round(sum(fs.energy) / (12 / (60 / n.interval_size)), 4), 0)) as energy
        FROM
            facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        JOIN network n on fs.network_id = n.code
        WHERE
            fs.is_forecast IS FALSE
            AND u.fueltech_id in ('solar_rooftop')
            AND fs.interval >= :start_time
            AND fs.interval <= :end_time
            {network_where_clause}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, n.interval_size
    ),
    facility_data as (
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
            round(sum(fs.energy_storage), 4) as energy_storage
        FROM
            facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        JOIN fueltech ft ON ft.code = u.fueltech_id
        JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
        WHERE
            fs.is_forecast IS FALSE
            AND u.fueltech_id not in ('solar_rooftop', 'imports', 'exports', 'interconnector', 'battery')
            AND fs.interval >= :start_time
            AND fs.interval <= :end_time
            {network_where_clause}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
    ),
    combined_data AS (
        -- Regular facility data
        SELECT
            fd.interval,
            fd.network_id,
            fd.network_region,
            fd.facility_code,
            fd.unit_code,
            fd.status_id,
            fd.fueltech_id,
            fd.fueltech_group_id,
            fd.renewable,
            fd.generated,
            fd.energy,
            fd.energy_storage,
            u.emissions_factor_co2
        FROM
            facility_data fd
        JOIN units u ON fd.unit_code = u.code

        UNION ALL

        -- Solar data (rooftop and utility)
        SELECT
            sd.interval,
            sd.network_id,
            sd.network_region,
            sd.facility_code,
            sd.unit_code,
            sd.status_id,
            sd.fueltech_id,
            sd.fueltech_group_id,
            sd.renewable,
            sd.generated,
            sd.energy,
            NULL as energy_storage,
            u.emissions_factor_co2
        FROM
            filled_solar_data sd
        JOIN units u ON sd.unit_code = u.code
    )
    SELECT
        cd.interval,
        cd.network_id,
        cd.network_region,
        cd.facility_code,
        cd.unit_code,
        cd.status_id,
        cd.fueltech_id,
        cd.fueltech_group_id,
        cd.renewable,
        cd.generated,
        cd.energy,
        cd.energy_storage,
        CASE
            WHEN cd.energy > 0 THEN coalesce(round(cd.emissions_factor_co2 * cd.energy, 4), 0)
            ELSE 0
        END as emissions,
        CASE
            WHEN cd.energy > 0 THEN coalesce(round(cd.emissions_factor_co2, 4), 0)
            ELSE 0
        END as emission_factor,
        CASE
            WHEN cd.energy > 0 THEN round(cd.energy * bs.price, 4)
            ELSE 0
        END as market_value
    FROM
        combined_data cd
    LEFT JOIN filled_balancing_summary bs ON
        bs.interval = cd.interval
        AND bs.network_region = cd.network_region
    WHERE
        cd.interval >= :start_time
        AND cd.interval < :end_time
        and cd.network_id not in ('OPENNEM_ROOFTOP_BACKFILL')
    ORDER BY 1,2,3,4,5
    """)

    result = await session.execute(query, {"start_time": start_time_naive, "end_time": end_time_naive})
    return result.fetchall()


async def _stream_unit_interval_data(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    network: NetworkSchema | None = None,
    batch_size: int = 20000,
) -> AsyncIterator[list[tuple]]:
    """
    Stream unit interval data from PostgreSQL in batches to reduce memory usage.

    Args:
        session: Database session
        start_time: Start time for data range
        end_time: End date for data range
        network: Optional network filter
        batch_size: Number of records per batch

    Yields:
        Batches of tuples containing unit interval data
    """
    # Strip timezone info
    start_time_naive = start_time.replace(tzinfo=None)
    end_time_naive = end_time.replace(tzinfo=None)

    network_where_clause = ""

    if network:
        network_codes = "','".join(network.get_network_codes())
        network_where_clause = f"AND fs.network_id IN ('{network_codes}')"

    # Base query without ORDER BY for better performance
    base_query = f"""
    WITH price_data AS (
        -- First get only the non-NULL price points
        SELECT
            interval,
            network_id,
            network_region,
            demand,
            demand_total,
            price
        FROM balancing_summary
        WHERE
            interval >= :start_time
            AND interval <= :end_time
            AND price IS NOT NULL
    ),
    filled_balancing_summary AS (
        -- Now gap-fill and carry forward the 30-minute prices to 5-minute intervals
        SELECT
            time_bucket_gapfill('5 minutes', pd.interval, :start_time, :end_time) as interval,
            pd.network_id,
            pd.network_region,
            locf(avg(pd.demand)) AS demand,
            locf(avg(pd.demand_total)) as demand_total,
            locf(avg(pd.price)) AS price
        FROM price_data pd
        GROUP BY 1, 2, 3
    ),
    filled_solar_data AS (
        SELECT
            time_bucket_gapfill('5 minutes', fs.interval) as interval,
            fs.network_id,
            f.network_region,
            f.code as facility_code,
            u.code as unit_code,
            u.status_id,
            u.fueltech_id,
            'solar' as fueltech_group_id,
            TRUE as renewable,
            locf(coalesce(round(sum(fs.generated), 4), 0)) as generated,
            locf(coalesce(round(sum(fs.energy) / (12 / (60 / n.interval_size)), 4), 0)) as energy
        FROM
            facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        JOIN network n on fs.network_id = n.code
        WHERE
            fs.is_forecast IS FALSE
            AND u.fueltech_id in ('solar_rooftop')
            AND fs.interval >= :start_time
            AND fs.interval <= :end_time
            {network_where_clause}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, n.interval_size
    ),
    facility_data as (
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
            round(sum(fs.energy_storage), 4) as energy_storage
        FROM
            facility_scada fs
        JOIN units u ON fs.facility_code = u.code
        JOIN facilities f ON u.station_id = f.id
        JOIN fueltech ft ON ft.code = u.fueltech_id
        JOIN fueltech_group ftg ON ftg.code = ft.fueltech_group_id
        WHERE
            fs.is_forecast IS FALSE
            AND u.fueltech_id not in ('solar_rooftop', 'imports', 'exports', 'interconnector', 'battery')
            AND fs.interval >= :start_time
            AND fs.interval <= :end_time
            {network_where_clause}
        GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
    ),
    combined_data AS (
        -- Regular facility data
        SELECT
            fd.interval,
            fd.network_id,
            fd.network_region,
            fd.facility_code,
            fd.unit_code,
            fd.status_id,
            fd.fueltech_id,
            fd.fueltech_group_id,
            fd.renewable,
            fd.generated,
            fd.energy,
            fd.energy_storage,
            u.emissions_factor_co2
        FROM
            facility_data fd
        JOIN units u ON fd.unit_code = u.code

        UNION ALL

        -- Solar data (rooftop and utility)
        SELECT
            sd.interval,
            sd.network_id,
            sd.network_region,
            sd.facility_code,
            sd.unit_code,
            sd.status_id,
            sd.fueltech_id,
            sd.fueltech_group_id,
            sd.renewable,
            sd.generated,
            sd.energy,
            NULL as energy_storage,
            u.emissions_factor_co2
        FROM
            filled_solar_data sd
        JOIN units u ON sd.unit_code = u.code
    )
    SELECT
        cd.interval,
        cd.network_id,
        cd.network_region,
        cd.facility_code,
        cd.unit_code,
        cd.status_id,
        cd.fueltech_id,
        cd.fueltech_group_id,
        cd.renewable,
        cd.generated,
        cd.energy,
        cd.energy_storage,
        CASE
            WHEN cd.energy > 0 THEN coalesce(round(cd.emissions_factor_co2 * cd.energy, 4), 0)
            ELSE 0
        END as emissions,
        CASE
            WHEN cd.energy > 0 THEN coalesce(round(cd.emissions_factor_co2, 4), 0)
            ELSE 0
        END as emission_factor,
        CASE
            WHEN cd.energy > 0 THEN round(cd.energy * bs.price, 4)
            ELSE 0
        END as market_value
    FROM
        combined_data cd
    LEFT JOIN filled_balancing_summary bs ON
        bs.interval = cd.interval
        AND bs.network_region = cd.network_region
    WHERE
        cd.interval >= :start_time
        AND cd.interval < :end_time
        and cd.network_id not in ('OPENNEM_ROOFTOP_BACKFILL')
    """

    params = {"start_time": start_time_naive, "end_time": end_time_naive}

    # Use server-side cursor for more efficient streaming
    order_clause = "ORDER BY cd.interval, cd.network_id, cd.network_region, cd.facility_code, cd.unit_code"
    full_query = text(f"{base_query} {order_clause}")

    # Execute query once and stream results
    result = await session.execute(full_query, params)

    while True:
        # Fetch batch using server-side cursor
        batch = result.fetchmany(batch_size)

        if not batch:
            break

        logger.debug(f"Fetched batch: {len(batch)} records")
        yield batch

        # Monitor memory usage between batches
        _monitor_memory_usage()

    # Close the result to free resources
    result.close()


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
            "energy_storage": pl.Float64,
            "emissions": pl.Float64,
            "emission_factor": pl.Float64,
            "market_value": pl.Float64,
        },
    )

    # Round numeric values to 4 decimal places
    numeric_cols = ["generated", "energy", "energy_storage", "emissions", "emission_factor", "market_value"]
    df = df.with_columns([pl.col(col).round(4) for col in numeric_cols])

    # Add version column based on current timestamp
    df = df.with_columns(pl.lit(int(datetime.now().timestamp())).alias("version"))

    # if network_region is SNOWY1 then set it to NSW1
    df = df.with_columns(
        pl.when(pl.col("network_region") == "SNOWY1")
        .then(pl.lit("NSW1"))
        .otherwise(pl.col("network_region"))
        .alias("network_region")
    )

    # filter out solar and renewable records before 26 October 2015
    # df = df.filter(
    #     (pl.col("fueltech_group_id") != "solar") | (pl.col("interval") >= datetime.fromisoformat("2015-10-26T00:00:00"))
    # )

    # # filter out wind records before we had non-scheduled generation data on 2009-07-01
    # df = df.filter(
    #     (pl.col("fueltech_group_id") != "wind") | (pl.col("interval") >= datetime.fromisoformat("2009-07-01T00:00:00"))
    # )

    # Ensure columns are in the exact order matching the table schema
    result_df = df.select(
        [
            "interval",
            "network_id",
            "network_region",
            "facility_code",
            "unit_code",
            "status_id",
            "fueltech_id",
            "fueltech_group_id",
            "renewable",
            "generated",
            "energy",
            "energy_storage",
            "emissions",
            "emission_factor",
            "market_value",
            "version",
        ]
    )

    # Convert back to list of tuples for ClickHouse insertion
    return result_df.rows()


def _ensure_clickhouse_schema() -> None:
    """
    Ensure ClickHouse schema exists by creating tables and views if needed.
    """
    client = get_clickhouse_client()
    if not table_exists(client, "unit_intervals"):
        create_table_if_not_exists(client, "unit_intervals", UNIT_INTERVALS_TABLE_SCHEMA)
        logger.info("Created unit_intervals")

    # Use the generic function to ensure materialized views exist
    ensure_materialized_views_exist(_UNIT_INTERVALS_MATERIALIZED_VIEWS)


def _refresh_clickhouse_schema() -> None:
    """
    Refresh ClickHouse schema by dropping and recreating tables and views.
    """
    print("This will drop and recreate all unit_intervals tables and views. Are you sure you want to continue? (y/n)")
    if input().lower() != "y":
        logger.info("User cancelled")
        return

    client = get_clickhouse_client()

    # Drop views first (in reverse order of creation to handle dependencies)
    for view in reversed(_UNIT_INTERVALS_MATERIALIZED_VIEWS):
        client.execute(f"DROP TABLE IF EXISTS {view.name}")
        logger.info(f"Dropped {view.name}")

    client.execute("DROP TABLE IF EXISTS unit_intervals")
    logger.info("Dropped unit_intervals")

    _ensure_clickhouse_schema()


async def process_unit_intervals_backlog(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    chunk_size: timedelta = timedelta(days=3),
    network: NetworkSchema | None = None,
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
    _ensure_clickhouse_schema()

    logger.info(f"Processing unit intervals from {current_start} to {end_date} for network {network.code if network else 'all'}")

    while current_start <= end_date:
        # For the last chunk, ensure we include the full end date
        chunk_end = min(current_start + chunk_size, end_date + timedelta(minutes=5))

        # Get and process data for this chunk
        records = await _get_unit_interval_data(session, current_start, chunk_end, network)
        if records:
            prepared_data = _prepare_unit_interval_data(records)

            # Batch insert into ClickHouse
            client.execute(
                """
                INSERT INTO unit_intervals
                (
                    interval, network_id, network_region, facility_code, unit_code,
                    status_id, fueltech_id, fueltech_group_id, renewable,
                    generated, energy, energy_storage, emissions, emission_factor, market_value,
                    version
                )
                VALUES
                """,
                prepared_data,
            )

            logger.info(f"Processed {len(prepared_data)} records from {current_start} to {chunk_end}")
        else:
            logger.warning(f"No records found for {current_start} to {chunk_end}")

        current_start = chunk_end


async def process_unit_intervals_backlog_streaming(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    chunk_size: timedelta = timedelta(days=3),
    batch_size: int = 20000,
    network: NetworkSchema | None = None,
) -> int:
    """
    Process historical unit interval data in chunks using streaming to reduce memory usage.

    Args:
        session: Database session
        start_date: Start date for processing
        end_date: End date for processing
        chunk_size: Size of each processing chunk
        batch_size: Number of records per batch within each chunk
        network: Optional network filter

    Returns:
        Total number of records processed
    """
    current_start = start_date
    client = get_clickhouse_client()
    _ensure_clickhouse_schema()
    total_processed = 0

    logger.info(
        f"Processing unit intervals (streaming) from {current_start} to {end_date} "
        f"for network {network.code if network else 'all'} "
        f"(chunk_size: {chunk_size}, batch_size: {batch_size})"
    )

    while current_start <= end_date:
        # For the last chunk, ensure we include the full end date
        chunk_end = min(current_start + chunk_size, end_date + timedelta(minutes=5))
        chunk_processed = 0

        logger.info(f"Processing chunk: {current_start} to {chunk_end}")
        _monitor_memory_usage()

        # Stream process this chunk in batches
        try:
            async for batch in _stream_unit_interval_data(session, current_start, chunk_end, network, batch_size):
                if batch:
                    prepared_data = _prepare_unit_interval_data(batch)

                    # Batch insert into ClickHouse
                    client.execute(
                        """
                        INSERT INTO unit_intervals
                        (
                            interval, network_id, network_region, facility_code, unit_code,
                            status_id, fueltech_id, fueltech_group_id, renewable,
                            generated, energy, energy_storage, emissions, emission_factor, market_value,
                            version
                        )
                        VALUES
                        """,
                        prepared_data,
                    )

                    chunk_processed += len(prepared_data)
                    logger.debug(f"Processed batch: {len(prepared_data)} records")
        except Exception as e:
            logger.error(f"Error processing chunk {current_start} to {chunk_end}: {e}")
            # Continue with next chunk rather than failing completely
            pass

        if chunk_processed > 0:
            logger.info(f"Processed {chunk_processed} records from {current_start} to {chunk_end}")
            total_processed += chunk_processed
        else:
            logger.warning(f"No records found for {current_start} to {chunk_end}")

        current_start = chunk_end

        # Force garbage collection between chunks
        gc.collect()

    logger.info(f"Total processed: {total_processed} records")
    return total_processed


async def run_unit_intervals_aggregate_to_now() -> int:
    """
    Run the unit intervals aggregation from the last processed interval to now.

    Returns:
        int: Number of records processed
    """
    client = get_clickhouse_client()

    # get the max interval from unit_intervals using FINAL modifier
    result = client.execute("SELECT MAX(interval) FROM unit_intervals FINAL")
    max_interval = result[0][0]

    date_from = max_interval + timedelta(minutes=5)
    date_to = get_last_completed_interval_for_network(network=NetworkNEM)

    if date_from > date_to:
        logger.info("No new data to process")
        return 0

    if date_from - date_to > timedelta(days=1):
        logger.info("Date range is greater than 1 day, skipping")
        return 0

    # run unit intervals from max_interval to now
    async with get_write_session() as session:
        records = await _get_unit_interval_data(session, date_from, date_to)
        prepared_data = _prepare_unit_interval_data(records)

    client.execute(
        """
        INSERT INTO unit_intervals
        (
            interval, network_id, network_region, facility_code, unit_code,
            status_id, fueltech_id, fueltech_group_id, renewable,
            generated, energy, energy_storage, emissions, emission_factor, market_value,
            version
        )
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
        (
            interval, network_id, network_region, facility_code, unit_code,
            status_id, fueltech_id, fueltech_group_id, renewable,
            generated, energy, energy_storage, emissions, emission_factor, market_value,
            version
        )
        VALUES
        """,
        prepared_data,
    )

    logger.info(f"Processed {len(prepared_data)} records from {start_date} to {end_date}")

    return len(prepared_data)


async def run_unit_intervals_aggregate_for_last_days(days: int) -> int:
    """
    Run the unit intervals aggregation for the last days.
    """
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)
    start_date = end_date - timedelta(days=days)

    async with get_write_session() as session:
        await process_unit_intervals_backlog(session=session, start_date=start_date, end_date=end_date)


async def run_unit_intervals_backlog(start_date: datetime | None = None, network: NetworkSchema | None = None) -> None:
    """
    Run the unit intervals aggregation for the history of the market.
    """
    # Calculate date range
    end_date = get_last_completed_interval_for_network(network=NetworkNEM)

    if not start_date and network:
        start_date = network.data_first_seen.replace(tzinfo=None)

    if not start_date:
        start_date = NetworkNEM.data_first_seen.replace(tzinfo=None)

    # Ensure ClickHouse schema exists
    client = get_clickhouse_client()

    # Process the data using streaming approach
    async with get_write_session() as session:
        total_processed = await process_unit_intervals_backlog_streaming(
            session=session,
            start_date=start_date,
            end_date=end_date,
            chunk_size=timedelta(days=7),
            batch_size=200000,
            network=network,
        )
        logger.info(f"Backlog processing complete: {total_processed} total records processed")

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
            f"Network: {network_id}, Region: {region}, Records: {count}, Period: {first.isoformat()} to {last.isoformat()}"
        )


async def _solar_and_wind_fixes() -> None:
    """
    Fix solar and wind records before 2015-10-26 and 2009-07-01 respectively.
    """
    client = get_clickhouse_client(timeout=100)

    client.execute("""
        delete from unit_intervals where fueltech_group_id = 'solar' and interval < '2016-08-01T00:00:00'
    """)

    client.execute(
        """
        DELETE FROM unit_intervals WHERE fueltech_group_id = 'wind' AND interval < '2009-07-01T00:00:00'
        """
    )


# Note: The backfill functions have been moved to the generic module
# opennem.db.clickhouse_materialized_views
# This function is kept for backward compatibility but delegates to the generic version


def backfill_unit_intervals_views(refresh_views: bool = False) -> None:
    """
    Backfill materialized views for unit_intervals data.
    This function delegates to the generic backfill_materialized_views function.

    Args:
        refresh_views: If True, drops and recreates views before backfilling.
    """
    # Use the generic function with unit_intervals specific views
    results = backfill_materialized_views(views=_UNIT_INTERVALS_MATERIALIZED_VIEWS, refresh_views=refresh_views)

    for view_name, count in results.items():
        logger.info(f"Backfilled {view_name}: {count} records")


if __name__ == "__main__":
    # Run the test
    async def reset_unit_intervals():
        _refresh_clickhouse_schema()
        # await run_unit_intervals_backlog(start_date=NetworkNEM.data_first_seen.replace(tzinfo=None))

        await run_unit_intervals_backlog(start_date=datetime.fromisoformat("2023-01-01T00:00:00"))
        await _solar_and_wind_fixes()

        await optimize_clickhouse_tables()

        # Uncomment to backfill views:
        backfill_unit_intervals_views(refresh_views=True)

    # asyncio.run(reset_unit_intervals())

    backfill_unit_intervals_views(refresh_views=True)
