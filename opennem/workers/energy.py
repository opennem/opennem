import asyncio
import logging
import multiprocessing
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem import settings
from opennem.db import get_read_session, get_write_session
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_datetime_now_for_network, get_today_opennem

logger = logging.getLogger("opennem.workers.energy")


async def _calculate_energy_for_interval(session: AsyncSession, start_time: datetime, end_time: datetime) -> int:
    """
    Calculate energy for a an interval range and update the energy column in the facility_scada table.

    The energy calculation requires both the current and previous interval's generated values
    to compute the average power over the interval. We explicitly exclude the first interval
    in each facility's range since we won't have access to its previous value.
    """

    query = text("""
    WITH
    network_data AS (
        SELECT
            code,
            interval_size,
            (60 / interval_size) as intervals_per_hour
        FROM network
    ),
    ranked_scada AS (
        SELECT
            network_id,
            facility_code,
            interval,
            generated,
            LAG(generated, 1) OVER (
                PARTITION BY network_id, facility_code
                ORDER BY interval
            ) AS prev_generated
        FROM facility_scada
        WHERE interval BETWEEN :start_time AND :end_time
    )
    UPDATE facility_scada fs
    SET
        energy = (rs.generated + rs.prev_generated) / 2 / nd.intervals_per_hour,
        energy_quality_flag = 2
    FROM ranked_scada rs
    JOIN network_data nd ON nd.code = rs.network_id
    WHERE fs.network_id = rs.network_id
      AND fs.facility_code = rs.facility_code
      AND fs.interval = rs.interval
      AND fs.interval BETWEEN :start_time AND :end_time
      -- Only update where we have both current and previous values
      AND rs.prev_generated IS NOT NULL
    """)

    result = await session.execute(query, {"start_time": start_time, "end_time": end_time})
    await session.commit()
    return result.rowcount  # type: ignore


async def run_energy_calculation_for_interval(interval: datetime) -> int:
    """
    Run energy calculation for a single interval.
    This method is intended to be called by a cron job every 5 minutes.
    """
    async with get_write_session() as session:
        start_time = interval
        end_time = interval + timedelta(minutes=5)

        if settings.dry_run:
            logger.debug(f"Dry run: Skipping calculation for {start_time} to {end_time}")
            return 0

        return await _calculate_energy_for_interval(session, start_time, end_time)


async def process_energy_from_now(hours: int = 2) -> None:
    """
    Process energy calculations from now.

    Defaults to running the last 2 hours.
    """

    async with get_write_session() as session:
        end_time = get_datetime_now_for_network(network=NetworkNEM, tz_aware=False).replace(tzinfo=None)
        start_time = end_time - timedelta(hours=hours)

        logger.info(f"Processing energy calculations from {start_time} to {end_time}")

        await _calculate_energy_for_interval(session=session, start_time=start_time, end_time=end_time)


def _chunk_date_range(start_date: datetime, end_date: datetime, chunk_size: timedelta) -> list[tuple[datetime, datetime]]:
    chunks = []
    current_start = start_date
    while current_start < end_date:
        chunk_end = min(current_start + chunk_size, end_date)
        chunks.append((current_start, chunk_end))
        current_start = chunk_end
    return chunks


async def _process_date_range(
    date_start: datetime, date_end: datetime, chunk_size: timedelta = timedelta(days=7), max_workers: int | None = None
):
    """
    Process a date range in chunks.
    """
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()

    chunks = _chunk_date_range(date_start, date_end, chunk_size)

    semaphore = asyncio.Semaphore(max_workers)

    async def process_chunk(chunk: tuple[datetime, datetime]):
        async with semaphore:
            start, end = chunk
            async with get_write_session() as session:
                if settings.dry_run:
                    logger.debug(f"Dry run: Skipping calculation for {start} to {end}")
                    return

                rows_updated = await _calculate_energy_for_interval(session, start, end)
                logger.info(f"Processed chunk {start} to {end}. Rows updated: {rows_updated}")

    tasks = [process_chunk(chunk) for chunk in chunks]
    await asyncio.gather(*tasks)


async def _get_energy_start_end_dates() -> tuple[datetime, datetime]:
    """
    Get the start and end dates for energy calculations.
    """
    async with get_read_session() as session:
        # Find the earliest date with null energy values
        query = text("SELECT MIN(interval) FROM facility_scada WHERE energy IS NULL")
        result = await session.execute(query)
        start_date = result.scalar()

        if not start_date:
            raise Exception("No backlog to process.")

        # Get the latest date in the facility_scada table
        query = text("SELECT MAX(interval) FROM facility_scada")
        result = await session.execute(query)
        end_date = result.scalar()

        if not end_date:
            raise Exception("No end date found.")

    return start_date, end_date


async def run_energy_backlog(date_start: datetime | None = None, date_end: datetime | None = None) -> None:
    """
    Run energy calculation for all historical data that hasn't been processed yet.
    """

    date_start_scada, date_end_scada = await _get_energy_start_end_dates()

    if date_start is None:
        date_start = date_start_scada

    if date_end is None:
        date_end = date_end_scada

    logger.info(f"Processing backlog from {date_start} to {date_end}")

    await _process_date_range(date_start=date_start, date_end=date_end)


# Example usage
async def main():
    # Process the most recent 5-minute interval

    # Run backlog
    print("Processing backlog...")
    date_start = datetime.fromisoformat("2019-09-25 00:00:00")
    date_end = get_today_opennem().replace(tzinfo=None)
    await run_energy_backlog(date_start=date_start, date_end=date_end)
    await process_energy_from_now()


if __name__ == "__main__":
    asyncio.run(process_energy_from_now(hours=1))
