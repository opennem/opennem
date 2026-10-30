"""Integrity check for #780: APVI WA rooftop days that stop mid-day.

APVI only publishes daylight intervals, so a normal WA day ends at dusk with its last row at
or near 0 MW. A day whose last row is still large and lands before mid-afternoon was cut off
at the source (2024-11-25 stopped at 10:30 on 1,076 MW). The read side now leaves that gap
NULL instead of carrying the value forward, and the `apvi.latest.data` refresh re-fetches it
for a week in case APVI completes it, so this check only alerts. It never writes.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import sentry_sdk
from sqlalchemy import text

from opennem.db import get_read_session
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import get_last_completed_interval_for_network

logger = logging.getLogger("opennem.monitors.apvi_truncation")

APVI_WA_UNIT = "ROOFTOP_APVI_WA"
# a last daylight row above this is still mid-generation, not a dusk tail
TRUNCATED_MIN_MW = 300.0
# a day whose last row lands before this (WEM network time) stopped before dusk
TRUNCATED_BEFORE = time(16, 0)
# whole days checked, ending yesterday (today is still being published)
LOOKBACK_DAYS = 7

_LAST_ROW_QUERY = text("""
    select distinct on (interval::date)
        interval::date as day,
        interval as last_interval,
        generated as last_generated
    from facility_scada
    where
        facility_code = :unit_code
        and is_forecast is false
        and interval >= :window_start
        and interval < :window_end
    order by interval::date, interval desc
""")


@dataclass(frozen=True, slots=True)
class TruncatedDay:
    day: date
    last_interval: datetime
    last_generated: float

    def __str__(self) -> str:
        return f"{self.day} ends {self.last_interval:%H:%M} on {self.last_generated:,.0f} MW"


def get_check_window(now: datetime) -> tuple[datetime, datetime]:
    """(start, end) naive WEM-time bounds: the LOOKBACK_DAYS whole days before today."""
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=LOOKBACK_DAYS), today


def is_truncated(last_interval: datetime, last_generated: float | None) -> bool:
    """A day is truncated when its last row is still above TRUNCATED_MIN_MW before TRUNCATED_BEFORE."""
    if last_generated is None:
        return False

    return float(last_generated) > TRUNCATED_MIN_MW and last_interval.time() < TRUNCATED_BEFORE


def find_truncated_days(rows: list[tuple[date, datetime, float | None]]) -> list[TruncatedDay]:
    """Pick the truncated days out of (day, last_interval, last_generated) rows."""
    return [
        TruncatedDay(day=day, last_interval=last_interval, last_generated=float(last_generated or 0))
        for day, last_interval, last_generated in rows
        if is_truncated(last_interval, last_generated)
    ]


async def run_apvi_truncation_check(now: datetime | None = None) -> list[TruncatedDay]:
    """Warn and send a sentry message for each truncated APVI WA day in the window. Read only."""
    if now is None:
        now = get_last_completed_interval_for_network(network=NetworkWEM, tz_aware=False)

    window_start, window_end = get_check_window(now)

    async with get_read_session() as session:
        rows = (
            await session.execute(
                _LAST_ROW_QUERY,
                {"unit_code": APVI_WA_UNIT, "window_start": window_start, "window_end": window_end},
            )
        ).all()

    truncated = find_truncated_days([(r[0], r[1], r[2]) for r in rows])

    if not truncated:
        logger.info(f"apvi truncation check clean: {len(rows)} days checked")
        return truncated

    summary = "; ".join(str(t) for t in truncated)
    logger.warning(f"APVI WA rooftop truncated at source on {len(truncated)} days: {summary}")

    with sentry_sdk.new_scope() as scope:
        scope.fingerprint = ["apvi-wa-rooftop-truncated"]
        scope.set_tag("days", str(len(truncated)))
        scope.set_context("apvi_truncation", {"days": [str(t) for t in truncated]})
        scope.capture_message(f"apvi wa rooftop truncated: {summary}", level="warning")

    return truncated
