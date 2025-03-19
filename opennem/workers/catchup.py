"""
OpenNEM Catchup Worker

This module provides functionality to detect data gaps in facility data and trigger catchup processes.
It monitors the last seen times for facilities and initiates crawlers and aggregation processes
when data gaps are detected.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import logfire
from sqlalchemy import text

from opennem import settings
from opennem.aggregates.facility_interval import run_update_facility_aggregate_last_interval, update_facility_aggregate_last_hours
from opennem.aggregates.market_summary import (
    run_market_summary_aggregate_for_last_days,
    run_market_summary_aggregate_for_last_intervals,
)
from opennem.aggregates.network_flows_v3 import run_flows_for_last_days
from opennem.aggregates.unit_intervals import (
    run_unit_intervals_aggregate_for_last_days,
    run_unit_intervals_aggregate_for_last_intervals,
)
from opennem.clients.slack import slack_message
from opennem.controllers.export import run_export_all, run_export_energy_for_year
from opennem.core.crawlers.schema import CrawlerDefinition
from opennem.core.parsers.aemo.filenames import AEMODataBucketSize
from opennem.crawl import run_crawl
from opennem.crawlers.apvi import APVIRooftopTodayCrawler
from opennem.crawlers.nemweb import (
    AEMONEMDispatchActualGEN,
    AEMONEMNextDayDispatch,
    AEMONemwebDispatchIS,
    AEMONemwebRooftop,
    AEMONemwebRooftopForecast,
    AEMONemwebTradingIS,
    AEMONNemwebDispatchScada,
)
from opennem.crawlers.wemde import run_all_wem_crawlers
from opennem.db import get_read_session
from opennem.db.views import refresh_recent_aggregates
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkAU, NetworkNEM
from opennem.workers.energy import process_energy_last_days, process_energy_last_intervals
from opennem.workers.facility_data_seen import update_facility_seen_range
from opennem.workers.incident import create_incident, has_active_incident, resolve_incident

logger = logging.getLogger("opennem.workers.catchup")


async def check_facility_data_gaps(max_gap_minutes: int = 30) -> tuple[bool, datetime | None]:
    """
    Check for gaps in facility data by looking at the last_seen timestamps.

    Args:
        max_gap_minutes: Maximum allowable gap in minutes before triggering catchup

    Returns:
        tuple[bool, datetime | None]: (has_gap, last_seen_time)
        where has_gap indicates if a gap was detected and last_seen_time is the most recent data point
    """
    query = text(
        """
        SELECT max(data_last_seen) as last_seen
        FROM units u
        JOIN facilities f ON f.id = u.station_id
        WHERE u.status_id = 'operating'
        AND f.network_id = 'NEM'
        AND u.dispatch_type = 'GENERATOR'
        """
    )

    async with get_read_session() as session:
        result = await session.execute(query)
        last_seen: datetime | None = result.scalars().one_or_none()

        if not last_seen:
            logger.error("No facility last seen data found")
            return True, None

        # remove timezone info from last seen
        last_seen = last_seen.replace(tzinfo=None)

        current_time = datetime.now(ZoneInfo("Australia/Brisbane")).replace(tzinfo=None)
        gap_minutes = (current_time - last_seen).total_seconds() / 60

        logger.debug(f"Last seen: {last_seen}, Current time: {current_time}, Gap: {gap_minutes:.1f} minutes")

        has_gap = gap_minutes > max_gap_minutes

        if has_gap:
            logger.warning(f"Data gap detected - Last seen: {last_seen}, Gap: {gap_minutes:.1f} minutes")

        return has_gap, last_seen


@logfire.instrument("task_catchup_check")
async def run_catchup_check(max_gap_minutes: int = 30) -> None:
    """
    Check for data gaps and trigger catchup processes if needed.

    Args:
        max_gap_minutes: Maximum allowable gap in minutes before triggering catchup
    """
    # Check if there's already an active incident
    if await has_active_incident():
        logger.info("Skipping catchup check - there is already an active incident")
        return

    has_gap, last_seen = await check_facility_data_gaps(max_gap_minutes=max_gap_minutes)

    if not has_gap:
        logger.info("No data gaps detected")
        return

    if not last_seen:
        logger.error("No last seen data found")
        return

    datetime_now = datetime.now(ZoneInfo("Australia/Brisbane")).replace(tzinfo=None, microsecond=0)

    # Create a new incident
    await create_incident(start_time=datetime_now, last_seen=last_seen)

    # Create a new incident
    await create_incident(start_time=datetime_now, last_seen=last_seen)

    # Alert about the gap
    gap_msg = (
        f"[{settings.env.upper()}] Data gap detected - Last seen: {last_seen.replace(tzinfo=None, microsecond=None)},",
        f" Current time: {datetime_now.replace(tzinfo=None, microsecond=None)}",
    )
    logger.warning(gap_msg)

    try:
        await slack_message(
            webhook_url=settings.slack_hook_monitoring,
            message=gap_msg,
            tag_users=settings.slack_admin_alert,
        )
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")

    # Run immediate data crawlers
    crawlers = [
        AEMONNemwebDispatchScada,
        AEMONemwebDispatchIS,
        AEMONemwebTradingIS,
        AEMONemwebRooftop,
        AEMONemwebRooftopForecast,
        APVIRooftopTodayCrawler,
    ]

    for crawler in crawlers:
        try:
            await run_crawl(crawler, latest=True)
        except Exception as e:
            logger.error(f"Error running crawler {crawler.__name__}: {e}")

    time_gap = datetime_now - last_seen

    # Run historical crawlers if gap is large
    if last_seen and time_gap > timedelta(hours=3):
        historical_crawlers = [
            AEMONEMDispatchActualGEN,
            AEMONEMNextDayDispatch,
        ]

        for crawler in historical_crawlers:
            try:
                await run_crawl(crawler, latest=True, limit=3, reverse=True)
            except Exception as e:
                logger.error(f"Error running historical crawler {crawler.__name__}: {e}")

    # run wem crawlers
    await run_all_wem_crawlers(latest=False, limit=7)

    # Update facility seen ranges
    try:
        await update_facility_seen_range()
    except Exception as e:
        logger.error(f"Error updating facility seen ranges: {e}")

    # calculate number of intervals to look back
    num_intervals = int(time_gap.total_seconds() / 300)

    # run energy calculation
    await process_energy_last_intervals(num_intervals=num_intervals)

    # run facility aggregate updates
    await run_update_facility_aggregate_last_interval(num_intervals=num_intervals)

    # Check if the gap is now resolved
    has_gap, _ = await check_facility_data_gaps(max_gap_minutes=max_gap_minutes)

    if not has_gap:
        # Mark the incident as resolved
        resolution_time = datetime.now(ZoneInfo("Australia/Brisbane")).replace(tzinfo=None)
        await resolve_incident(resolution_time)

        # Send resolution notification
        resolution_msg = f"[{settings.env.upper()}] Data gap resolved at {resolution_time}"
        logger.info(resolution_msg)
        try:
            await slack_message(
                webhook_url=settings.slack_hook_monitoring,
                message=resolution_msg,
                tag_users=settings.slack_admin_alert,
            )
        except Exception as e:
            logger.error(f"Failed to send resolution Slack alert: {e}")


def _get_limit_for_crawler(crawler: CrawlerDefinition, days: int) -> int:
    """Get the limit for a crawler"""
    match crawler.bucket_size:
        case AEMODataBucketSize.interval:
            return days * 12 * 24
        case AEMODataBucketSize.half_hour:
            return days * 2 * 24
        case AEMODataBucketSize.day:
            return days
        case AEMODataBucketSize.week:
            return days * 7
        case AEMODataBucketSize.fortnight:
            return days * 14
        case AEMODataBucketSize.month:
            return days * 30
        case AEMODataBucketSize.year:
            return days * 365
        case _:
            return days * 12 * 24


async def catchup_last_days(days: int = 1):
    """Run a catchup for the last 24 hours"""

    crawlers = [
        AEMONNemwebDispatchScada,
        AEMONemwebDispatchIS,
        AEMONemwebTradingIS,
        AEMONemwebRooftop,
        AEMONemwebRooftopForecast,
        AEMONEMDispatchActualGEN,
        AEMONEMNextDayDispatch,
    ]

    for crawler in crawlers:
        await run_crawl(crawler, latest=False, limit=_get_limit_for_crawler(crawler, days))

        if days > crawler.contains_days:
            await run_crawl(
                crawler.archive_version, latest=False, reverse=True, limit=_get_limit_for_crawler(crawler.archive_version, days)
            )

    # run aggregates
    await process_energy_last_days(days=days)
    await run_unit_intervals_aggregate_for_last_days(days=days)
    await run_market_summary_aggregate_for_last_days(days=days)
    run_flows_for_last_days(days=days, network=NetworkNEM)
    await update_facility_aggregate_last_hours(hours_back=days * 24)

    # refresh materialized views
    await refresh_recent_aggregates(days_back=days + 1)

    # run exports
    CURRENT_YEAR = datetime.now(ZoneInfo("Australia/Brisbane")).year

    await asyncio.gather(
        run_export_energy_for_year(year=CURRENT_YEAR),
        run_export_energy_for_year(year=CURRENT_YEAR - 1),
    )

    await run_export_all()


async def catchup_last_intervals(num_intervals: int = 12):
    """Run a catchup for the last 24 hours"""

    crawlers = [
        AEMONNemwebDispatchScada,
        AEMONemwebDispatchIS,
        AEMONemwebTradingIS,
        AEMONemwebRooftop,
        AEMONemwebRooftopForecast,
    ]

    for crawler in crawlers:
        await run_crawl(crawler, latest=False, limit=num_intervals)

    await process_energy_last_intervals(num_intervals=num_intervals)

    await run_unit_intervals_aggregate_for_last_intervals(num_intervals=num_intervals)
    await run_market_summary_aggregate_for_last_intervals(num_intervals=num_intervals)

    run_flows_for_last_days(days=3, network=NetworkNEM)

    await update_facility_aggregate_last_hours(hours_back=num_intervals / 12)

    await asyncio.gather(
        run_export_power_latest_for_network(network=NetworkNEM), run_export_power_latest_for_network(network=NetworkAU)
    )

    CURRENT_YEAR = datetime.now(ZoneInfo("Australia/Brisbane")).year

    await asyncio.gather(
        run_export_energy_for_year(year=CURRENT_YEAR),
        run_export_energy_for_year(year=CURRENT_YEAR - 1),
    )

    await run_export_all()


if __name__ == "__main__":
    import asyncio

    # asyncio.run(run_catchup_check(max_gap_minutes=15))
    asyncio.run(catchup_last_days(days=4))
