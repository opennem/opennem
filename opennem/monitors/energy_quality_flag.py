"""Regression guard for #764: NEM energy that never left the generated/12 fallback.

The energy worker replaces the fallback energy with the trapezoid value and sets `energy_quality_flag = 2`.
Anything older than a few days that is still below 2 means a reprocess window missed a write that reset the flag
(that is exactly how #764 happened: the next-day dispatch upsert reset it for days the worker never revisited).

A handful of rows legitimately stay below 2 (the first interval a unit ever reports has no previous value for the
formula), so the alert has a small threshold rather than firing on > 0.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import sentry_sdk
from sqlalchemy import text

from opennem import settings
from opennem.db import get_read_session
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.monitors.energy_quality_flag")

# rows newer than this are still inside the live reprocess windows
GRACE_DAYS = 3
# bound the scan: older than this is the backfill's job, and it keeps the query on the interval index
LOOKBACK_DAYS = 14

_UNPROCESSED_QUERY = text("""
    select
        date_trunc('day', interval) as day,
        count(*) as unprocessed
    from facility_scada
    where
        network_id = 'NEM'
        and is_forecast is false
        and energy_quality_flag < 2
        and interval >= :window_start
        and interval < :window_end
    group by 1
    order by 1
""")


@dataclass(frozen=True, slots=True)
class UnprocessedEnergy:
    total: int
    by_day: dict[str, int]

    def __str__(self) -> str:
        days = ", ".join(f"{d}: {n:,}" for d, n in self.by_day.items())
        return f"{self.total:,} NEM facility_scada rows older than {GRACE_DAYS}d have energy_quality_flag < 2 ({days})"


def exceeds_threshold(total: int, threshold: int) -> bool:
    """Alert only strictly above the threshold."""
    return total > threshold


def get_check_window(now: datetime) -> tuple[datetime, datetime]:
    """(start, end) naive NEM-time bounds of the rows to check."""
    return now - timedelta(days=LOOKBACK_DAYS), now - timedelta(days=GRACE_DAYS)


async def count_unprocessed_energy(now: datetime | None = None) -> UnprocessedEnergy:
    """Count flag < 2 NEM rows between LOOKBACK_DAYS and GRACE_DAYS old, per day."""
    if now is None:
        now = get_last_completed_interval_for_network(network=NetworkNEM, tz_aware=False).replace(tzinfo=None)

    window_start, window_end = get_check_window(now)

    async with get_read_session() as session:
        rows = (await session.execute(_UNPROCESSED_QUERY, {"window_start": window_start, "window_end": window_end})).all()

    by_day = {str(day)[:10]: int(count) for day, count in rows}
    return UnprocessedEnergy(total=sum(by_day.values()), by_day=by_day)


async def run_energy_quality_flag_check(now: datetime | None = None) -> UnprocessedEnergy | None:
    """Run the check, warn and send a sentry message above the threshold. Returns None when disabled."""
    if not settings.energy_flag_guard_enabled:
        logger.info("energy quality flag guard disabled")
        return None

    result = await count_unprocessed_energy(now=now)

    if not exceeds_threshold(result.total, settings.energy_flag_guard_threshold):
        logger.info(f"energy quality flag guard clean: {result.total} rows below flag 2")
        return result

    logger.warning(f"{result} (threshold {settings.energy_flag_guard_threshold})")

    with sentry_sdk.new_scope() as scope:
        scope.fingerprint = ["energy-quality-flag-unprocessed"]
        scope.set_tag("rows", str(result.total))
        scope.set_context("energy_quality_flag", {"total": result.total, "by_day": result.by_day})
        scope.capture_message(f"energy not reprocessed: {result}", level="warning")

    return result
