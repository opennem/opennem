"""Re-fetch the last week of APVI rooftop and re-aggregate the days that changed (#780).

The 15-minute `apvi.today.data` crawl only looks at today and yesterday. APVI sometimes
publishes a WA day truncated (2026-10-28 stopped at 07:45) and completes it later, so a day
that has rolled out of that window is never repaired. This re-fetches the 7-day
`apvi.latest.data` window (an idempotent upsert, one small request per day) and, only for
the days whose rows actually changed, re-aggregates the APVI rooftop unit into
unit_intervals so the repair reaches clickhouse.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import text

from opennem.aggregates.unit_intervals import process_unit_intervals_backlog
from opennem.crawl import run_crawl
from opennem.crawlers.apvi import APVIRooftopLatestCrawler
from opennem.db import get_read_session, get_write_session
from opennem.schema.network import NetworkAPVI, NetworkWEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.workers.apvi_latest")

LOOKBACK_DAYS = APVIRooftopLatestCrawler.contains_days or 7

# per-day fingerprint of the stored APVI actuals; a change after the re-fetch means the day
# was corrected upstream and must be re-aggregated
_FINGERPRINT_QUERY = text("""
    select
        interval::date as day,
        count(*) as row_count,
        coalesce(round(sum(generated)::numeric, 3), 0) as generated_sum
    from facility_scada
    where
        network_id = 'APVI'
        and is_forecast is false
        and interval >= :window_start
    group by 1
""")

DayFingerprint = dict[date, tuple[int, float]]


@dataclass(frozen=True, slots=True)
class ApviLatestResult:
    changed_days: list[date]
    window: tuple[datetime, datetime] | None


async def _fingerprint(window_start: datetime) -> DayFingerprint:
    async with get_read_session() as session:
        rows = (await session.execute(_FINGERPRINT_QUERY, {"window_start": window_start})).all()

    return {day: (int(row_count), float(generated_sum)) for day, row_count, generated_sum in rows}


def changed_days(before: DayFingerprint, after: DayFingerprint) -> list[date]:
    """Days whose row count or summed generation differs between the two fingerprints."""
    return sorted(day for day in set(before) | set(after) if before.get(day) != after.get(day))


def reaggregate_window(days: list[date], now: datetime) -> tuple[datetime, datetime] | None:
    """Naive network-time window covering the changed days, plus the next day.

    The rooftop carry-forward bounds night buckets by the next real reading, so the day after
    the last changed one is re-aggregated too. Never extends past `now`.
    """
    if not days:
        return None

    start = datetime.combine(min(days), datetime.min.time())
    end = min(datetime.combine(max(days), datetime.min.time()) + timedelta(days=2), now)

    if end <= start:
        return None

    return start, end


async def run_apvi_latest_refresh(now: datetime | None = None) -> ApviLatestResult:
    """Re-crawl the last week of APVI and re-aggregate only the days that changed."""
    if now is None:
        now = get_last_completed_interval_for_network(network=NetworkWEM, tz_aware=False)

    window_start = (now - timedelta(days=LOOKBACK_DAYS + 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    before = await _fingerprint(window_start)
    await run_crawl(APVIRooftopLatestCrawler)
    after = await _fingerprint(window_start)

    days = changed_days(before, after)
    window = reaggregate_window(days, now)

    if not window:
        logger.info("apvi latest refresh: no days changed")
        return ApviLatestResult(changed_days=days, window=None)

    logger.info(f"apvi latest refresh: {len(days)} days changed ({', '.join(str(d) for d in days)}), re-aggregating {window}")

    async with get_write_session() as session:
        await process_unit_intervals_backlog(
            session=session,
            start_date=window[0],
            end_date=window[1],
            network=NetworkAPVI,
        )

    return ApviLatestResult(changed_days=days, window=window)
