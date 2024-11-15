import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import get_write_session
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network, get_today_opennem

logger = logging.getLogger("opennem.aggregates.facility_interval")


async def update_facility_aggregates(
    db_session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
) -> None:
    """
    Updates facility aggregates for the given time range.
    Uses an INSERT ... ON CONFLICT DO UPDATE approach for efficient upserts.
    """
    try:
        # The aggregation query
        query = text("""
            WITH filled_balancing_summary AS (
                SELECT
                    time_bucket_gapfill(
                        '5 minutes'::interval,
                        bs.interval
                    ) AS interval,
                    bs.network_id,
                    bs.network_region,
                    locf(
                        avg(bs.demand)
                    ) AS demand,
                    locf(
                        avg(bs.price)
                    ) AS price
                FROM balancing_summary bs
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
                    AND bs.network_id = fs.network_id
                    AND bs.network_region = f.network_region
            WHERE
                fs.is_forecast IS FALSE
                AND u.fueltech_id IS NOT NULL
                AND u.fueltech_id NOT IN ('imports', 'exports', 'interconnector', 'battery')
                AND fs.interval >= :start_time
                AND fs.interval <= :end_time
            GROUP BY 1, 2, 3, 4, 5, 6, 7
            ON CONFLICT (interval, network_id, facility_code, unit_code)
            DO UPDATE SET
                generated = EXCLUDED.generated,
                energy = EXCLUDED.energy,
                emissions = EXCLUDED.emissions,
                emissions_intensity = EXCLUDED.emissions_intensity,
                market_value = EXCLUDED.market_value,
                last_updated = EXCLUDED.last_updated
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
) -> None:
    """
    Process a single chunk of facility aggregates with semaphore control

    Args:
        semaphore (asyncio.Semaphore): Semaphore to control concurrent executions
        start_time (datetime): Start time for the chunk
        end_time (datetime): End time for the chunk
    """
    async with semaphore:
        async with get_write_session() as session:
            await update_facility_aggregates(session, start_time, end_time)


async def run_update_facility_intervals(hours: int = 4) -> None:
    """
    Updates facility intervals for the last x hours (default 4)

    """
    end_time = get_today_opennem().replace(second=0, microsecond=0, tzinfo=None)
    start_time = end_time - timedelta(hours=hours)
    async with get_write_session() as session:
        await update_facility_aggregates(session, start_time, end_time)


async def update_facility_aggregates_chunked(
    start_date: datetime,
    end_date: datetime,
    chunk_days: int = 30,
    max_concurrent: int = 2,
) -> None:
    """
    Updates facility aggregates in chunks working backwards from end_time to start_time.
    Processes multiple chunks concurrently to improve performance.

    Args:
        start_date (datetime): Start date for updates
        end_date (datetime): End date for updates
        chunk_days (int): Number of days to process in each chunk
        max_concurrent (int): Maximum number of concurrent update operations
    """
    # Create chunks
    chunks: list[tuple[datetime, datetime]] = []
    current_end = end_date

    # strip timzones
    start_date = start_date.replace(tzinfo=None)
    end_date = end_date.replace(tzinfo=None)

    while current_end > start_date:
        current_start = current_end - timedelta(days=chunk_days)

        # Ensure we don't go before our target start time
        if current_start < start_date:
            current_start = start_date

        chunks.append((current_start, current_end))
        current_end = current_start - timedelta(days=1)

    # Create semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(max_concurrent)

    # Create tasks for all chunks
    tasks = [_process_aggregate_chunk(semaphore, chunk_start, chunk_end) for chunk_start, chunk_end in chunks]

    logger.info(f"Processing {len(chunks)} chunks with max {max_concurrent} concurrent operations")

    try:
        # Execute all tasks and wait for completion
        await asyncio.gather(*tasks)
        logger.info("All chunks processed successfully")
    except Exception as e:
        logger.error(f"Error during parallel processing: {str(e)}")
        raise


async def run_facility_aggregate_updates(
    lookback_days: int | None = None,
    chunk_days: int = 30,
    max_concurrent: int = 4,
) -> None:
    """
    Main function to run facility aggregate updates for a specified time range

    Args:
        lookback_days (Optional[int]): Number of days to look back from current time.
            If None, defaults to 30 minutes
        chunk_days (int): Number of days to process in each chunk when processing historical data
        max_concurrent (int): Maximum number of concurrent update operations
    """
    try:
        end_time = get_today_opennem().replace(second=0, microsecond=0)

        if lookback_days:
            start_time = end_time - timedelta(days=lookback_days)
            await update_facility_aggregates_chunked(
                start_time,
                end_time,
                chunk_days=chunk_days,
                max_concurrent=max_concurrent,
            )
        else:
            # Default behaviour - just update last 30 minutes
            start_time = end_time - timedelta(minutes=30)
            async with get_write_session() as session:
                await update_facility_aggregates(session, start_time, end_time)

    except Exception as e:
        logger.error(f"Error in aggregate update: {str(e)}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example: Update last 7 days of data in chunks
    # asyncio.run(run_facility_aggregate_updates(lookback_days=7))
    interval = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None)

    # asyncio.run(
    #     update_facility_aggregates_chunked(
    #         start_date=interval - timedelta(days=7),
    #         end_date=interval,
    #         chunk_days=30,
    #     )
    # )

    asyncio.run(run_update_facility_intervals(hours=24))
