import asyncio
import logging
from datetime import date, datetime, time, timedelta

import logfire
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import get_write_session
from opennem.schema.network import NetworkAEMORooftop, NetworkNEM, NetworkSchema, NetworkWEM, NetworkWEMDE
from opennem.utils.dates import get_last_completed_interval_for_network, get_today_opennem

logger = logging.getLogger("opennem.aggregates.facility_interval")


async def update_facility_aggregates(
    db_session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    network: NetworkSchema | None = None,
) -> None:
    """
    Updates facility aggregates for the given time range using partition-aware approach.
    Uses an INSERT ... ON CONFLICT DO UPDATE with improved locking strategy.

    Args:
        db_session (AsyncSession): Database session
        start_time (datetime): Start time for aggregation
        end_time (datetime): End time for aggregation
        network (NetworkSchema | None): Optional network to filter by
    """
    network_filter = ""

    # normalize the time to be without timezone info
    start_time = start_time.replace(tzinfo=None, second=0, microsecond=0)
    end_time = end_time.replace(tzinfo=None, second=0, microsecond=0)

    if end_time <= start_time:
        raise Exception("Start time must be before end time")

    if network:
        network_filter = f"AND fs.network_id = '{network.code}'"

    try:
        # The optimized aggregation query with improved locking strategy
        query = text(f"""
            WITH filled_balancing_summary AS (
                SELECT
                    time_bucket_gapfill('5 minutes', bs.interval) as interval,
                    bs.network_id,
                    bs.network_region,
                    locf(
                        avg(bs.demand)
                    ) AS demand,
                    locf(
                        avg(bs.price)
                    ) AS price
                FROM mv_balancing_summary bs
                WHERE
                    bs.interval >= :start_time
                    AND bs.interval <= :end_time
                GROUP BY 1, 2, 3
            )
            INSERT INTO at_facility_intervals (
                interval,
                network_id,
                facility_code,
                unit_code,
                fueltech_code,
                network_region,
                status_id,
                generated,
                energy,
                emissions,
                emissions_intensity,
                market_value,
                last_updated
            )
            SELECT
                time_bucket('5 minutes', fs.interval),
                fs.network_id,
                f.code,
                fs.facility_code,
                u.fueltech_id,
                f.network_region,
                u.status_id,
                round(sum(fs.generated), 4),
                round(sum(fs.energy), 4),
                CASE
                    WHEN sum(fs.energy) > 0 THEN coalesce(round(sum(u.emissions_factor_co2 * fs.energy), 4), 0)
                    ELSE 0
                END,
                CASE
                    WHEN sum(fs.energy) > 0 THEN coalesce(round(sum(u.emissions_factor_co2 * fs.energy) / sum(fs.energy), 4), 0)
                    ELSE 0
                END,
                CASE
                    WHEN sum(fs.energy) > 0 THEN round(sum(fs.energy) * max(bs.price), 4)
                    ELSE 0
                END,
                now()
            FROM
                facility_scada fs
                JOIN units u ON fs.facility_code = u.code
                JOIN facilities f ON u.station_id = f.id
                LEFT JOIN filled_balancing_summary bs ON
                    bs.interval = fs.interval
                    AND bs.network_region = f.network_region
            WHERE
                fs.is_forecast IS FALSE
                AND u.fueltech_id IS NOT NULL
                AND u.fueltech_id NOT IN ('imports', 'exports', 'interconnector', 'battery')
                AND fs.interval >= :start_time
                AND fs.interval < :end_time
                {network_filter}
            GROUP BY 1, 2, 3, 4, 5, 6, 7
            ON CONFLICT (interval, network_id, facility_code, unit_code)
            DO UPDATE SET
                generated = EXCLUDED.generated,
                energy = EXCLUDED.energy,
                emissions = EXCLUDED.emissions,
                emissions_intensity = EXCLUDED.emissions_intensity,
                market_value = EXCLUDED.market_value,
                last_updated = EXCLUDED.last_updated
            WHERE at_facility_intervals.last_updated < EXCLUDED.last_updated
        """)

        await db_session.execute(
            query,
            {
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        await db_session.commit()

        logger.info(f"Updated facility aggregates from {start_time} to {end_time}")

    except Exception as e:
        await db_session.rollback()
        logger.error(f"Error updating facility aggregates: {str(e)}")
        raise


async def _process_aggregate_chunk(
    semaphore: asyncio.Semaphore,
    start_time: datetime,
    end_time: datetime,
    network: NetworkSchema | None = None,
) -> None:
    """
    Process a single chunk of facility aggregates with semaphore control and retry logic

    Args:
        semaphore (asyncio.Semaphore): Semaphore to control concurrent executions
        start_time (datetime): Start time for the chunk
        end_time (datetime): End time for the chunk
        network (NetworkSchema | None): Optional network to filter by
    """
    async with semaphore:
        async with get_write_session() as session:
            await update_facility_aggregates(session, start_time, end_time, network=network)


@logfire.instrument("update_facility_aggregate_last_hours")
async def update_facility_aggregate_last_hours(hours_back: int = 1, network: NetworkSchema | None = None) -> None:
    """
    Updates facility aggregates for the current day, looking back a specified number of hours.
    This is designed to be called frequently to keep current day data up to date.

    Args:
        days_back (int): Number of days to look back from current day
    """
    end_time = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None) + timedelta(minutes=5)
    start_time = end_time - timedelta(hours=hours_back)

    async with get_write_session() as session:
        await update_facility_aggregates(session, start_time, end_time, network=network)


async def run_update_facility_aggregate_last_interval(num_intervals: int = 6) -> None:
    """
    Runs the facility aggregate update for the last 30 minute interval
    """
    end_time = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None) + timedelta(minutes=5)
    start_time = end_time - timedelta(minutes=num_intervals * 5)

    async with get_write_session() as session:
        await update_facility_aggregates(session, start_time, end_time)


async def update_facility_aggregates_chunked(
    start_date: date,
    end_date: date,
    chunk_days: int = 30,
    max_concurrent: int = 2,
    network: NetworkSchema | None = None,
) -> None:
    """
    Updates facility aggregates in chunks working backwards from end_date to start_date.
    Processes multiple chunks concurrently to improve performance.

    Args:
        start_date (date): Start date for updates
        end_date (date): End date for updates
        chunk_days (int): Number of days to process in each chunk
        max_concurrent (int): Maximum number of concurrent update operations
        network (NetworkSchema | None): Optional network to filter by
    """
    # Convert dates to datetime bounds
    start_dt = datetime.combine(start_date, time.min).replace(second=0, microsecond=0, tzinfo=None)
    end_dt = datetime.combine(end_date, time.max).replace(second=0, microsecond=0, tzinfo=None)

    if start_dt >= end_dt:
        raise Exception("Start date should be earlier than end date")

    # Create chunks
    chunks: list[tuple[datetime, datetime]] = []
    current_end = end_dt

    while current_end > start_dt:
        current_start = current_end - timedelta(days=chunk_days)

        # Ensure we don't go before our target start time
        if current_start < start_dt:
            current_start = start_dt

        chunks.append((current_start, current_end))
        current_end = current_start - timedelta(microseconds=1)  # Ensure no overlap

    # Create semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_concurrent)

    # Create tasks for all chunks
    tasks = [_process_aggregate_chunk(semaphore, chunk_start, chunk_end, network=network) for chunk_start, chunk_end in chunks]

    logger.info(f"Processing {len(chunks)} chunks with max {max_concurrent} concurrent operations")

    try:
        await asyncio.gather(*tasks)
        logger.info("All chunks processed successfully")
    except Exception as e:
        logger.error(f"Error during parallel processing: {str(e)}")
        raise


async def run_facility_aggregate_updates(
    lookback_days: int | None = None,
    chunk_days: int = 30,
    max_concurrent: int = 4,
    network: NetworkSchema | None = None,
) -> None:
    """
    Main function to run facility aggregate updates for a specified time range

    Args:
        lookback_days (int | None): Number of days to look back from current time.
            If None, defaults to current day only
        chunk_days (int): Number of days to process in each chunk when processing historical data
        max_concurrent (int): Maximum number of concurrent update operations
        network (NetworkSchema | None): Optional network to filter by
    """
    try:
        today = get_today_opennem().date()

        if lookback_days:
            start_date = today - timedelta(days=lookback_days)
            await update_facility_aggregates_chunked(
                start_date,
                today,
                chunk_days=chunk_days,
                max_concurrent=max_concurrent,
                network=network,
            )
        else:
            # Default behaviour - just update current day
            await update_facility_aggregate_last_hours(network=network)

    except Exception as e:
        logger.error(f"Error in aggregate update: {str(e)}")
        raise


async def run_facility_aggregate_for_network(network: NetworkSchema, chunk_days: int = 30, max_concurrent: int = 2) -> None:
    """Run facility aggregate updates for a specific network.

    This function calculates and updates facility aggregate data from the
    first date data was seen for the given network up to the last completed
    interval.

    Args:
        network (NetworkSchema): The network for which to run aggregate updates.

    Raises:
        Exception: If the network's data_first_seen attribute is not set.
    """

    if not network.data_first_seen:
        raise Exception("Network data first seen is not set")

    end_date = get_last_completed_interval_for_network(network=network).replace(tzinfo=None)

    await update_facility_aggregates_chunked(
        start_date=network.data_first_seen,
        end_date=end_date,
        chunk_days=chunk_days,
        max_concurrent=max_concurrent,
        network=network,
    )


async def run_facility_aggregate_all(chunk_days: int = 30, max_concurrent: int = 2) -> None:
    """Run facility aggregate updates for all networks"""
    start_date = NetworkNEM.data_first_seen
    end_date = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None)

    await update_facility_aggregates_chunked(
        start_date=start_date,  # type: ignore
        end_date=end_date,
        chunk_days=chunk_days,
        max_concurrent=max_concurrent,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example: Update last 7 days of data in chunks
    # asyncio.run(run_facility_aggregate_updates(lookback_days=7))
    interval = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None)
    nem_start = NetworkNEM.data_first_seen.replace(tzinfo=None)  # type: ignore
    rooftop_start = NetworkAEMORooftop.data_first_seen.replace(tzinfo=None)  # type: ignore

    up_to_interval = datetime.fromisoformat("2003-06-16T00:00:00")

    asyncio.run(
        update_facility_aggregates_chunked(
            start_date=NetworkWEMDE.data_first_seen,
            end_date=interval,
            max_concurrent=2,
            chunk_days=3,
            network=NetworkWEM,
        )
    )
