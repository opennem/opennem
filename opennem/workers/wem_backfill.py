"""Backfill WEM facility generation from the AEMO facility-scada archive.

AEMO only began publishing the `EOI Quantity (MW)` column in the WEM facility-scada
archive on 2013-12-17. OpenNEM derived `generated` solely from that column, so every WEM
unit has null generation and energy before that date even though the archive carries
`Energy Generated (MWh)` all the way back to 2006-09 (see #598).

The client now derives power from the published energy for that era. This worker walks
the monthly archive files and persists them.

Note on eras:

  * 2006-09 .. 2023-09  legacy archive, 30 minute trading intervals
  * 2023-10 ..          WEMDE, 5 minute dispatch intervals, handled by
                        `opennem.crawlers.wemde` and not touched here

Interval size is detected per file rather than assumed, so a cadence change upstream does
not silently corrupt the energy/power conversion.
"""

import asyncio
import logging
from datetime import datetime

from opennem.clients.wem import WEMFileNotFoundException, get_wem_facility_intervals
from opennem.controllers.wem import store_wem_facility_intervals

logger = logging.getLogger("opennem.workers.wem_backfill")

# First month present in the AEMO facility-scada archive
WEM_ARCHIVE_FIRST_MONTH = datetime(2006, 9, 1)

# Last month for which the legacy archive is the source of truth. WEMDE starts
# 2023-10-01, so October 2023 onward belongs to opennem.crawlers.wemde and must not be
# ingested through the 30-minute legacy path.
WEM_ARCHIVE_LAST_MONTH = datetime(2023, 9, 1)

# Last month affected by the missing EOI Quantity column, and so the default end of the
# backfill. Everything after this already has generation from the published MW column.
WEM_EOI_QUANTITY_LAST_MONTH = datetime(2013, 12, 1)


def _month_range(date_start: datetime, date_end: datetime) -> list[datetime]:
    """Inclusive list of month-start dates between two dates"""
    months = []
    current = date_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = date_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    while current <= end:
        months.append(current)
        current = (
            current.replace(year=current.year + 1, month=1) if current.month == 12 else current.replace(month=current.month + 1)
        )

    return months


async def run_wem_facility_scada_backfill(
    date_start: datetime = WEM_ARCHIVE_FIRST_MONTH,
    date_end: datetime = WEM_EOI_QUANTITY_LAST_MONTH,
    dry_run: bool = False,
    fill_nulls_only: bool = True,
) -> int:
    """Backfill WEM facility scada from the monthly archive.

    Defaults to filling nulls only, so a month straddling the 2013-12-17 EOI cutover can
    be re-ingested without overwriting generation or energy that is already published.

    Returns the total number of records persisted.
    """
    if date_end > WEM_ARCHIVE_LAST_MONTH:
        logger.warning(
            f"Clamping date_end {date_end:%Y-%m} to {WEM_ARCHIVE_LAST_MONTH:%Y-%m} - WEMDE is the source after the cutover"
        )
        date_end = WEM_ARCHIVE_LAST_MONTH

    months = _month_range(date_start, date_end)

    if not months:
        logger.warning(f"No months to backfill: date_start {date_start:%Y-%m} is after date_end {date_end:%Y-%m}")
        return 0

    logger.info(f"Backfilling WEM facility scada for {len(months)} months: {months[0]:%Y-%m} to {months[-1]:%Y-%m}")

    total_records = 0

    for month in months:
        try:
            # fallback_to_recent would silently substitute a recent month for a missing
            # one, which for a backfill means ingesting the wrong period entirely
            interval_set = await get_wem_facility_intervals(from_date=month, fallback_to_recent=False)
        except WEMFileNotFoundException:
            logger.warning(f"{month:%Y-%m}: no archive file, skipping")
            continue
        except Exception as e:
            logger.error(f"{month:%Y-%m}: download or parse failed: {e}")
            continue

        if not interval_set.intervals:
            logger.warning(f"{month:%Y-%m}: no intervals parsed, skipping")
            continue

        with_generated = len([i for i in interval_set.intervals if i.generated is not None])
        interval_size = interval_set.intervals[0].interval_size_minutes

        if dry_run:
            logger.info(
                f"{month:%Y-%m}: [dry run] {len(interval_set.intervals)} intervals "
                f"({with_generated} with generation) at {interval_size}min"
            )
            continue

        cr = await store_wem_facility_intervals(interval_set, created_by="wem_backfill", fill_nulls_only=fill_nulls_only)

        total_records += cr.inserted_records

        logger.info(
            f"{month:%Y-%m}: stored {cr.inserted_records} of {len(interval_set.intervals)} intervals "
            f"({with_generated} with generation) at {interval_size}min, {cr.errors} errors"
        )

        if cr.error_detail:
            logger.error(f"{month:%Y-%m}: {cr.error_detail}")

    logger.info(f"Backfill complete, {total_records} records persisted")

    return total_records


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Backfill WEM facility scada from the AEMO archive")
    parser.add_argument("--date-start", type=lambda s: datetime.strptime(s, "%Y-%m"), default=WEM_ARCHIVE_FIRST_MONTH)
    parser.add_argument("--date-end", type=lambda s: datetime.strptime(s, "%Y-%m"), default=WEM_EOI_QUANTITY_LAST_MONTH)
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing values instead of filling nulls only")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    await run_wem_facility_scada_backfill(
        date_start=args.date_start, date_end=args.date_end, dry_run=args.dry_run, fill_nulls_only=not args.overwrite
    )


if __name__ == "__main__":
    asyncio.run(main())
