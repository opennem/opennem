import asyncio
import logging
import multiprocessing
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem import settings
from opennem.db import get_write_session
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.workers.energy")


async def _calculate_energy_for_interval(session: AsyncSession, start_time: datetime, end_time: datetime) -> int:
    """
    Calculate energy for a an interval range and update the energy column in the facility_scada table.

    The energy calculation requires both the current and previous interval's generated values
    to compute the average power over the interval. We explicitly exclude the first interval
    in each facility's range since we won't have access to its previous value.

    We also exclude WEM, WEMDE and AEMO_ROOFTOP_BACKFILL since they have their own energy calculations
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
        WHERE
            interval BETWEEN :lag_start AND :end_time
            AND network_id not in ('WEM', 'WEMDE', 'AEMO_ROOFTOP_BACKFILL')
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
      AND fs.energy_quality_flag < 2
      AND rs.prev_generated IS NOT NULL
    """)

    lag_start = start_time - timedelta(minutes=5)
    result = await session.execute(query, {"start_time": start_time, "end_time": end_time, "lag_start": lag_start})
    await session.commit()
    return result.rowcount  # type: ignore


async def run_energy_calculation_for_interval(interval: datetime) -> int:
    """
    Run energy calculation for a single interval.
    This method is intended to be called by a cron job every 5 minutes.
    """
    async with get_write_session() as session:
        start_time = interval - timedelta(minutes=5)
        end_time = interval + timedelta(minutes=5)

        if settings.dry_run:
            logger.debug(f"Dry run: Skipping calculation for {start_time} to {end_time}")
            return 0

        return await _calculate_energy_for_interval(session, start_time, end_time)


async def process_energy_last_intervals(num_intervals: int = 6) -> None:
    """
    Process energy calculations for the last num_intervals intervals.

    This is intended to be run by a cron job every 5 minutes.

    params:
        num_intervals: int = 6 - the number of 5 minute intervals to process back from the last completed interval

    returns:
        None
    """

    end_time = get_last_completed_interval_for_network(network=NetworkNEM, tz_aware=False).replace(tzinfo=None)
    start_time = end_time - timedelta(minutes=5 * num_intervals)

    logger.info(f"Processing energy calculations from {start_time} to {end_time}")

    async with get_write_session() as session:
        await _calculate_energy_for_interval(session=session, start_time=start_time, end_time=end_time)


async def process_energy_last_days(days: int = 1):
    """
    Process energy calculations for the last days.
    """
    end_time = get_last_completed_interval_for_network(network=NetworkNEM, tz_aware=False).replace(tzinfo=None)
    start_time = end_time - timedelta(days=days)

    logger.info(f"Processing energy calculations from {start_time} to {end_time}")
    await _process_date_range(date_start=start_time, date_end=end_time)


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
        max_workers = min(4, multiprocessing.cpu_count())

    chunks = _chunk_date_range(date_start, date_end, chunk_size)

    semaphore = asyncio.Semaphore(max_workers)

    async def process_chunk(chunk: tuple[datetime, datetime]) -> int:
        async with semaphore:
            start, end = chunk
            async with get_write_session() as session:
                if settings.dry_run:
                    logger.debug(f"Dry run: Skipping calculation for {start} to {end}")
                    return 0

                rows_updated = await _calculate_energy_for_interval(session, start, end)
                logger.info(f"Processed chunk {start} to {end}. Rows updated: {rows_updated}")
                return rows_updated

    tasks = [process_chunk(chunk) for chunk in chunks]
    return sum(await asyncio.gather(*tasks))


# a next-day dispatch crawl with limit=3 can touch up to 3 trading days plus the day the first one starts in
MIN_DISPATCH_REPROCESS_WINDOW = timedelta(days=4)


def get_dispatch_reprocess_window(
    interval_min: datetime | None,
    interval_max: datetime | None,
    now: datetime,
    min_window: timedelta = MIN_DISPATCH_REPROCESS_WINDOW,
) -> tuple[datetime, datetime]:
    """Window the energy worker must redo after a next-day dispatch crawl reset energy_quality_flag (#764).

    The dispatch upsert resets flag and energy to the fallback on every row in the files it loads, so the worker has
    to redo exactly that span. When the crawl reports the span of the rows it wrote we use it (the lag interval the
    formula needs is added by `_calculate_energy_for_interval`); with no span (nothing reported) fall back to the
    conservative `min_window`. The window always ends at `now` (the last completed interval) so rows landed since
    are covered too. All datetimes are naive NEM time.
    """
    if interval_min is None:
        return now - min_window, now

    interval_min = interval_min.replace(tzinfo=None)
    start = interval_min if interval_min < now else now - min_window
    end = max(now, interval_max.replace(tzinfo=None)) if interval_max else now
    return start, end


async def reprocess_energy_window(
    date_start: datetime, date_end: datetime, chunk_size: timedelta = timedelta(days=1), max_workers: int = 2
) -> int:
    """Reprocess energy for an explicit window in day chunks and log how many rows were reprocessed."""
    logger.info(f"Reprocessing energy from {date_start} to {date_end}")
    rows = await _process_date_range(date_start=date_start, date_end=date_end, chunk_size=chunk_size, max_workers=max_workers)
    logger.info(f"Reprocessed energy from {date_start} to {date_end}: {rows} rows updated")
    return rows


async def run_energy_backlog(
    date_start: datetime, date_end: datetime, chunk_size: timedelta = timedelta(days=10), max_workers: int = 4
) -> int:
    """
    Run energy calculation for all historical data that hasn't been processed yet. Returns rows updated.
    """

    logger.info(f"Processing backlog from {date_start} to {date_end}")

    return await _process_date_range(date_start=date_start, date_end=date_end, chunk_size=chunk_size, max_workers=max_workers)


# Example usage
async def main():
    # Process the most recent 5-minute interval

    # Run backlog
    print("Processing backlog...")
    date_start = datetime.fromisoformat("2023-01-01 00:00:00")
    date_end = get_last_completed_interval_for_network().replace(tzinfo=None)

    print(f"Processing {date_start} to {date_end}")

    await run_energy_backlog(date_start=date_start, date_end=date_end)


if __name__ == "__main__":
    asyncio.run(main())
