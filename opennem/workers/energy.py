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


# MWh. A flag 2 NEM row whose energy is further than this from the trapezoid is stale (#767). energy is numeric(20,6)
# so rounding noise is ~1e-6, and the fallback (generated / 12) differs from the trapezoid by (generated - prev) / 24
ENERGY_REPAIR_TOLERANCE = 0.0005

# networks whose energy the worker never touches, they have their own energy calculations
_EXCLUDED_NETWORKS = "('WEM', 'WEMDE', 'AEMO_ROOFTOP_BACKFILL')"

# trapezoid only between ADJACENT intervals (#771). Sparse units (batteries, loads) omit zero rows, so the previous row can
# be hours earlier and must not feed the trapezoid. Without an adjacent previous row the energy is the fallback
# generated / intervals_per_hour. Single definition shared by the worker update, the repair count and the monitor.
# Needs `rs` (ranked_scada) and `nd` (network_data) in scope.
EXPECTED_ENERGY_SQL = """CASE
            WHEN rs.prev_interval = rs.interval - nd.interval_size * interval '1 minute'
                THEN (rs.generated + rs.prev_generated) / 2 / nd.intervals_per_hour
            ELSE rs.generated / nd.intervals_per_hour
        END"""

# lookback for the lag row: the longest network interval (30 min) so a row at the window start still finds its
# adjacent previous row. Anything further back is a gap by definition.
LAG_LOOKBACK = timedelta(minutes=30)

_RANKED_SCADA_CTE = f"""
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
            ) AS prev_generated,
            LAG(interval, 1) OVER (
                PARTITION BY network_id, facility_code
                ORDER BY interval
            ) AS prev_interval
        FROM facility_scada
        WHERE
            interval BETWEEN :lag_start AND :end_time
            AND network_id not in {_EXCLUDED_NETWORKS}
        )
"""

# rows of the window the worker must (re)write: not processed yet, or (NEM only) processed but holding something other
# than the trapezoid, which is what a re-delivery that overwrote energy with generated / 12 leaves behind (#767).
# NEM only because rooftop / APVI mix forecast and actual rows and 30 / 15 minute intervals in one lag partition,
# so their stored energy is not comparable to this formula. The predicate only runs on rows already restricted to
# the window by the interval range, it never widens the scan.
_NEEDS_ENERGY_UPDATE = f"""
      AND (
          fs.energy_quality_flag < 2
          OR (
              fs.network_id = 'NEM'
              AND (
                  fs.energy IS NULL
                  OR abs(fs.energy - ({EXPECTED_ENERGY_SQL})) > :energy_tolerance
              )
          )
      )
"""

ENERGY_UPDATE_QUERY = text(
    f"""
    WITH {_RANKED_SCADA_CTE}
    UPDATE facility_scada fs
    SET
        energy = {EXPECTED_ENERGY_SQL},
        energy_quality_flag = 2
    FROM ranked_scada rs
    JOIN network_data nd ON nd.code = rs.network_id
    WHERE fs.network_id = rs.network_id
      AND fs.facility_code = rs.facility_code
      AND fs.interval = rs.interval
      AND fs.interval BETWEEN :start_time AND :end_time
      {_NEEDS_ENERGY_UPDATE}
    """
)

# read-only: flag 2 NEM rows in the window whose energy is not the expected value (#771), what the update repairs
ENERGY_MISMATCH_COUNT_QUERY = text(
    f"""
    WITH {_RANKED_SCADA_CTE}
    SELECT count(*)
    FROM facility_scada fs
    JOIN ranked_scada rs
      ON fs.network_id = rs.network_id AND fs.facility_code = rs.facility_code AND fs.interval = rs.interval
    JOIN network_data nd ON nd.code = rs.network_id
    WHERE fs.network_id = 'NEM'
      AND fs.interval BETWEEN :start_time AND :end_time
      AND fs.energy_quality_flag = 2
      AND (
          fs.energy IS NULL
          OR abs(fs.energy - ({EXPECTED_ENERGY_SQL})) > :energy_tolerance
      )
    """
)


def _energy_params(start_time: datetime, end_time: datetime) -> dict[str, object]:
    return {
        "start_time": start_time,
        "end_time": end_time,
        "lag_start": start_time - LAG_LOOKBACK,
        "energy_tolerance": ENERGY_REPAIR_TOLERANCE,
    }


async def _calculate_energy_for_interval(session: AsyncSession, start_time: datetime, end_time: datetime) -> int:
    """
    Calculate energy for a an interval range and update the energy column in the facility_scada table.

    The trapezoid needs the generated value of the immediately previous interval. When the previous row is not exactly
    one interval earlier (sparse units, first row ever) the row gets the fallback generated / intervals_per_hour and
    flag 2 (#771), so it is considered processed and the self-heal below fixes it if the missing row arrives later.

    We also exclude WEM, WEMDE and AEMO_ROOFTOP_BACKFILL since they have their own energy calculations

    Self-healing (#767): NEM rows already at flag 2 whose energy is not the trapezoid (re-delivered scada overwrote it
    with generated / 12) are rewritten too, so any window the worker processes repairs itself.
    """
    result = await session.execute(ENERGY_UPDATE_QUERY, _energy_params(start_time, end_time))
    await session.commit()
    return result.rowcount  # type: ignore


async def count_energy_mismatches(session: AsyncSession, start_time: datetime, end_time: datetime) -> int:
    """Read-only count of flag 2 NEM rows in [start_time, end_time] whose energy is not the trapezoid (#767)."""
    return int((await session.execute(ENERGY_MISMATCH_COUNT_QUERY, _energy_params(start_time, end_time))).scalar_one())


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
