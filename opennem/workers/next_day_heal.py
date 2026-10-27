"""Self-heal for units that only arrive in the Next_Day_Dispatch file (#773).

Some NEM units are not in the live DISPATCH_SCADA feed. Their facility_scada rows come only from
DISPATCH_UNIT_SOLUTION in the next-day dispatch file, crawled once a day by `task_nem_per_day_check`
with `limit=3`. A missed cron run (max_tries=1, #726) leaves a hole that only heals if it is within
the last 3 files, and a missing zero-valued row inflates 30m+ power (5 intervals averaged, not 6).

This step counts rows per trading day for those units over the last 14 days, re-crawls the
next-day file for any short day, and alerts when a day is still short afterwards. The caller
reprocesses energy and re-aggregates clickhouse over the span the re-crawl wrote.
"""

import asyncio
import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy import bindparam, text

from opennem.controllers.schema import ControllerReturn
from opennem.core.parsers.dirlisting import DirlistingEntry

logger = logging.getLogger("opennem.workers.next_day_heal")

# units that are not in live DISPATCH_SCADA, only in the next-day DISPATCH_UNIT_SOLUTION (#773). Not derivable
# from config: the split battery codes look like any other battery_charging/discharging unit, so this is the
# single list to edit when AEMO adds or retires one.
NEXT_DAY_ONLY_UNITS: frozenset[str] = frozenset(
    {
        "SNOWYGJP",
        "KEPBG1",
        "KEPBL1",
        "WILLBESG1",
        "WILLBESL1",
        "WOORBG1",
        "MRNBESSG1",
        "MRNBESSL1",
        "TB3BG1",
        "TB3BL1",
    }
)

INTERVALS_PER_TRADING_DAY = 288
HEAL_WINDOW_DAYS = 14

# a NEM trading day D runs from D 04:05 to D+1 04:00 (interval-ending), which is what one next-day file holds
TRADING_DAY_OFFSET = timedelta(hours=4, minutes=5)

UnitDay = tuple[str, date]


@dataclass(frozen=True)
class ShortDay:
    unit_code: str
    trading_day: date
    rows: int

    def __str__(self) -> str:
        return f"{self.unit_code} {self.trading_day.isoformat()}: {self.rows}/{INTERVALS_PER_TRADING_DAY}"


@dataclass
class HealResult:
    short_before: list[ShortDay] = field(default_factory=list)
    short_after: list[ShortDay] = field(default_factory=list)
    days_crawled: list[date] = field(default_factory=list)
    days_without_file: list[date] = field(default_factory=list)
    crawl: ControllerReturn = field(default_factory=ControllerReturn)


# pure helpers


def trading_day_of(interval: datetime) -> date:
    """Trading day an interval-ending NEM timestamp belongs to (04:05 D .. 04:00 D+1 -> D)."""
    return (interval - TRADING_DAY_OFFSET).date()


def heal_window(last_completed_interval: datetime, days: int = HEAL_WINDOW_DAYS) -> list[date]:
    """The last `days` complete trading days, oldest first.

    The trading day `last_completed_interval` sits in is still open, so the window ends the day before it.
    """
    last_complete = trading_day_of(last_completed_interval) - timedelta(days=1)
    return [last_complete - timedelta(days=offset) for offset in range(days - 1, -1, -1)]


def trading_day_bounds(first_day: date, last_day: date) -> tuple[datetime, datetime]:
    """Exclusive start and inclusive end interval covering trading days first_day..last_day."""
    start = datetime.combine(first_day, datetime.min.time()) + TRADING_DAY_OFFSET - timedelta(minutes=5)
    end = datetime.combine(last_day + timedelta(days=1), datetime.min.time()) + TRADING_DAY_OFFSET - timedelta(minutes=5)
    return start, end


def find_short_days(
    counts: Mapping[UnitDay, int],
    units: Iterable[str],
    window: list[date],
    expected: int = INTERVALS_PER_TRADING_DAY,
) -> list[ShortDay]:
    """Unit-days in the window with fewer than `expected` rows.

    `counts` should also hold the day before the window. Two rules keep units a re-crawl can't fix out:
    - a unit is only checked if it has at least one full day, so a sparse unit (TB3BL1 had 381 rows in all of
      oct 2026, only dispatched some intervals) or one with no rows at all is never flagged. A whole missed file
      is still caught through the full units, and the re-crawl is per file so it heals the sparse ones too.
    - a unit is only expected from the day after the first day it has any rows (in the window or the day
      before), so one that started mid-window (commissioning, partial first day) is not flagged before it existed.
    """
    if not window:
        return []

    short: list[ShortDay] = []

    for unit in sorted(units):
        unit_counts = {day: rows for (code, day), rows in counts.items() if code == unit}
        seen_days = sorted(day for day, rows in unit_counts.items() if rows > 0)
        if not seen_days or max(unit_counts.values()) < expected:
            continue

        first_seen = seen_days[0]
        for day in window:
            if day <= first_seen:
                continue
            rows = unit_counts.get(day, 0)
            if rows < expected:
                short.append(ShortDay(unit_code=unit, trading_day=day, rows=rows))

    return short


def short_trading_days(short: Iterable[ShortDay]) -> list[date]:
    """Distinct trading days to re-crawl, oldest first."""
    return sorted({s.trading_day for s in short})


def select_entries_for_days(entries: Iterable[DirlistingEntry], days: Iterable[date]) -> dict[date, DirlistingEntry]:
    """Map each wanted trading day to its next-day dispatch file (named by trading day, eg _20261027_).

    When AEMO republishes a day the newest listed file wins.
    """
    wanted = set(days)
    selected: dict[date, DirlistingEntry] = {}

    for entry in entries:
        if not entry.aemo_interval_date or not entry.aemo_interval_date.date:
            continue
        day = entry.aemo_interval_date.date.date()
        if day not in wanted:
            continue
        current = selected.get(day)
        if current is None or entry.modified_date > current.modified_date:
            selected[day] = entry

    return selected


def extend_window_start(start: datetime, healed_min: datetime | None) -> datetime:
    """Pull an energy reprocess window start back to cover the span a heal re-crawl wrote (naive NEM time)."""
    if healed_min is None:
        return start
    return min(start, healed_min.replace(tzinfo=None))


def format_alert(short: list[ShortDay], days_without_file: list[date]) -> str:
    lines = "\n".join(f"• {s}" for s in short)
    message = (
        f"*Next-day dispatch units still short after self-heal* (#773)\n"
        f"These units only arrive in the Next_Day_Dispatch file, the re-crawl did not fill them:\n{lines}"
    )
    if days_without_file:
        missing = ", ".join(d.isoformat() for d in days_without_file)
        message += f"\nNo file in nemweb CURRENT for: {missing} (load from the Next_Day_Dispatch archive)"
    return message


# io


_COUNT_QUERY = text(
    """
    select
        fs.facility_code,
        date(fs.interval - interval '4 hours 5 minutes') as trading_day,
        count(*) as row_count
    from facility_scada fs
    where
        fs.network_id = 'NEM'
        and fs.is_forecast is false
        and fs.facility_code in :codes
        and fs.interval > :start
        and fs.interval <= :end
    group by 1, 2
    """
).bindparams(bindparam("codes", expanding=True))


async def count_unit_day_rows(units: Iterable[str], first_day: date, last_day: date) -> dict[UnitDay, int]:
    """facility_scada rows per (unit, trading day) for trading days first_day..last_day."""
    from opennem.db import get_read_session

    start, end = trading_day_bounds(first_day, last_day)
    params = {"codes": sorted(units), "start": start, "end": end}

    async with get_read_session() as session:
        rows = (await session.execute(_COUNT_QUERY, params)).all()

    return {(str(code), day): int(n) for code, day, n in rows}


async def _count_for_window(window: list[date]) -> dict[UnitDay, int]:
    # one extra day back anchors find_short_days' first-seen rule without dropping the oldest window day
    return await count_unit_day_rows(NEXT_DAY_ONLY_UNITS, window[0] - timedelta(days=1), window[-1])


async def recrawl_next_day_files(days: list[date]) -> tuple[ControllerReturn, list[date], list[date]]:
    """Re-crawl the next-day dispatch file for each trading day, sequentially.

    Returns the merged controller return, the days crawled and the days with no file in CURRENT.
    """
    from opennem.core.parsers.dirlisting import get_dirlisting
    from opennem.crawlers.nemweb import AEMONEMNextDayDispatch, process_nemweb_entry

    total = ControllerReturn()
    if not days or not AEMONEMNextDayDispatch.url:
        return total, [], list(days)

    dirlisting = await get_dirlisting(AEMONEMNextDayDispatch.url, timezone="Australia/Brisbane")
    selected = select_entries_for_days(dirlisting.get_files(), days)
    without_file = [d for d in days if d not in selected]
    crawled: list[date] = []

    for day in sorted(selected):
        entry = selected[day]
        logger.info(f"next-day heal: re-crawling {entry.link} for trading day {day}")
        try:
            result = await process_nemweb_entry(crawler=AEMONEMNextDayDispatch, entry=entry, max_date=entry.modified_date)
        except Exception as e:
            logger.error(f"next-day heal: re-crawl of {entry.link} failed: {e}")
            continue
        if not result:
            continue
        crawled.append(day)
        total.inserted_records += result.inserted_records
        total.processed_records += result.processed_records
        total.total_records += result.total_records
        total.merge_interval_span(result)

    return total, crawled, without_file


async def heal_next_day_units(last_completed_interval: datetime, days: int = HEAL_WINDOW_DAYS) -> HealResult:
    """Count, re-crawl the short days, recount. Energy and clickhouse are left to the caller (span in `crawl`)."""
    window = heal_window(last_completed_interval, days=days)
    result = HealResult()

    counts = await _count_for_window(window)
    result.short_before = find_short_days(counts, NEXT_DAY_ONLY_UNITS, window)

    if not result.short_before:
        logger.info(f"next-day heal: all next-day-only units complete for {window[0]}..{window[-1]}")
        return result

    to_crawl = short_trading_days(result.short_before)
    logger.warning(f"next-day heal: {len(result.short_before)} short unit-days over {len(to_crawl)} trading days, re-crawling")

    result.crawl, result.days_crawled, result.days_without_file = await recrawl_next_day_files(to_crawl)

    counts = await _count_for_window(window)
    result.short_after = find_short_days(counts, NEXT_DAY_ONLY_UNITS, window)
    return result


async def reaggregate_nem_window(start: datetime, end: datetime) -> None:
    """Push healed facility_scada rows to clickhouse, same steps as the catchup pass.

    unit_intervals, then every materialized view and the additive fueltech/region table over the window (late
    writes lose to the existing partial rows otherwise, #592/#763). Run after the energy redo so the energy
    values that land are the flag 2 ones.
    """
    from opennem.aggregates.fueltech_region_intervals import rebuild_range as rebuild_agg_range
    from opennem.aggregates.unit_intervals import process_unit_intervals_backlog
    from opennem.db import get_read_session
    from opennem.db.clickhouse.materialized_views import backfill_materialized_views
    from opennem.schema.network import NetworkNEM

    logger.info(f"next-day heal: re-aggregating clickhouse from {start} to {end}")

    async with get_read_session() as session:
        await process_unit_intervals_backlog(
            session=session, start_date=start, end_date=end, network=NetworkNEM, rebuild_daily_views=False
        )

    _ = await asyncio.to_thread(backfill_materialized_views, start_date=start, end_date=end, refresh_views=False)
    _ = await rebuild_agg_range(start, end)


async def alert_still_short(result: HealResult) -> bool:
    """Log and send the monitoring alert when the heal left unit-days short."""
    if not result.short_after:
        return False

    from opennem import settings
    from opennem.clients.slack import slack_message

    for s in result.short_after:
        logger.warning(f"next-day heal: still short {s}")

    return await slack_message(
        webhook_url=settings.slack_hook_monitoring,
        message=format_alert(result.short_after, result.days_without_file),
        tag_users=settings.slack_admin_alert,
    )
