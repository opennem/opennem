"""OpenNEM tasks"""

import asyncio
import logging

from arq import Retry

from opennem import settings
from opennem.aggregates.market_summary import run_market_summary_aggregate_to_now
from opennem.aggregates.unit_intervals import run_unit_intervals_aggregate_to_now
from opennem.api.export.tasks import export_all_daily, export_all_monthly, export_energy
from opennem.cms.importer import update_database_facilities_from_cms
from opennem.cms.updates import send_cms_updates_slack_report
from opennem.controllers.capacity_history import export_capacity_history_json
from opennem.controllers.export import run_export_energy_all, run_export_energy_for_year
from opennem.core.battery import check_unsplit_batteries
from opennem.crawl import run_crawl
from opennem.crawlers.aemo_market_notice import run_market_notice_update
from opennem.crawlers.apvi import APVIRooftopTodayCrawler
from opennem.crawlers.bom import BOMCapitals
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
from opennem.db.clickhouse_schema import optimize_clickhouse_tables
from opennem.exporter.facilities import export_facilities_static

# from opennem.exporter.historic import export_historic_intervals
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkAU, NetworkNEM, NetworkWEM
from opennem.utils.dates import get_today_opennem
from opennem.workers.catchup import catchup_aggregates, catchup_last_days, run_catchup_check
from opennem.workers.energy import process_energy_last_intervals
from opennem.workers.facility_data_seen import update_facility_seen_range
from opennem.workers.facility_first_seen import facility_first_seen_check
from opennem.workers.generation_max import update_max_generation_for_units
from opennem.workers.system import clean_tmp_dir
from opennem.workers.weekly_summary import run_weekly_summary

logger = logging.getLogger("opennem.pipelines.nem")

# crawl tasks


async def task_nem_interval_check(ctx) -> None:
    """This task runs per interval and checks for new data"""
    _ = await run_crawl(AEMONemwebDispatchIS, latest=True)
    _ = await run_crawl(AEMONNemwebDispatchScada, latest=True)
    _ = await run_crawl(AEMONemwebTradingIS, latest=True)

    # update energy
    await process_energy_last_intervals(num_intervals=12 * 3)

    # update aggregates (flows computed inline via market_summary when flows_v4=True)
    await run_market_summary_aggregate_to_now()
    await run_unit_intervals_aggregate_to_now()

    await asyncio.gather(
        run_export_power_latest_for_network(network=NetworkNEM), run_export_power_latest_for_network(network=NetworkAU)
    )


async def task_nem_per_day_check(ctx) -> None:
    """This task is run daily for NEM"""
    dispatch_actuals = await run_crawl(AEMONEMDispatchActualGEN, latest=True, limit=3)
    await run_crawl(AEMONEMNextDayDispatch, latest=True, limit=3)

    if not dispatch_actuals or not dispatch_actuals.inserted_records:
        raise Retry(defer=ctx["job_try"] * 15)

    # Next-day dispatch resets energy_quality_flag via upsert, so reprocess
    # energy for the last 48h to cover the dispatch window
    await process_energy_last_intervals(num_intervals=12 * 48)


async def task_nem_rooftop_crawl(ctx) -> None:
    """Runs the NEM rooftop crawler every rooftop interval (30 min)"""

    tasks = [
        run_crawl(AEMONemwebRooftop),
        run_crawl(AEMONemwebRooftopForecast),
    ]

    rooftop = await asyncio.gather(*tasks)

    if not rooftop or not any(r.inserted_records for r in rooftop if r):
        raise Retry(defer=ctx["job_try"] * 15)


async def task_update_max_generation_for_units(ctx) -> None:
    """This task runs daily to update the max generation for each unit"""
    await update_max_generation_for_units(days_since=2)


async def task_wem_day_crawl(ctx) -> None:
    """This task runs per interval and checks for new data"""
    await run_all_wem_crawlers(latest=True, limit=3)
    await run_export_power_latest_for_network(network=NetworkWEM)
    await run_export_energy_for_year(network=NetworkWEM)


async def task_apvi_crawl(ctx) -> None:
    """Runs the APVI crawler every 10 minutes"""
    await run_crawl(APVIRooftopTodayCrawler)


async def task_bom_capitals_crawl(ctx) -> None:
    """Runs the BOM Capitals crawler every 10 minutes"""
    await run_crawl(BOMCapitals)


#  processing tasks


async def task_run_energy_calculation(ctx) -> None:
    """Runs the energy calculation for the last 2 hours"""
    await process_energy_last_intervals(num_intervals=4)


async def task_facility_first_seen_check(ctx) -> None:
    """Runs the facility first seen check"""
    await facility_first_seen_check(send_slack=True, only_generation=True)


async def task_update_facility_seen_range(ctx) -> None:
    """Updates the facility seen range"""
    await update_facility_seen_range(interval_window_days=7)


async def task_update_facility_first_seen(ctx) -> None:
    """Updates the facility first seen"""
    await update_facility_seen_range(include_first_seen=True, interval_window_days=7)


# Output tasks


async def task_nem_power_exports(ctx) -> None:
    """Runs the NEM exports"""
    await asyncio.gather(
        run_export_power_latest_for_network(network=NetworkNEM),
        run_export_power_latest_for_network(network=NetworkAU),
        # run_export_power_latest_for_network(network=NetworkWEMDE),
    )


async def task_export_flows(ctx) -> None:
    """Runs the flows export"""
    pass
    # await export_electricitymap()
    # await export_flows()


async def task_export_energy(ctx) -> None:
    """Runs the energy export"""
    await export_energy(latest=True)

    current_date = get_today_opennem()

    # @NOTE new years day fix for energy exports - run last year and current year
    if current_date.day == 1 and current_date.month == 1:
        await run_export_energy_for_year(year=current_date.year - 1)
        await run_export_energy_for_year(year=current_date.year)

    await run_export_energy_all()


async def task_export_facility_geojson(ctx) -> None:
    """Exports the facility geojson"""
    await export_facilities_static()


# async def task_sync_archive_exports(ctx) -> None:
#     """Run and sync parquet exports to output bucket"""
#     await sync_archive_exports()
#     await generate_archive_dirlisting()


async def task_export_daily_monthly(ctx) -> None:
    """Runs the daily and monthly exports"""
    await export_all_daily()
    await export_all_monthly()


async def task_export_capacity_history(ctx) -> None:
    """Export capacity history data to JSON and upload to Cloudflare.

    Runs nightly to update the capacity history based on unit commencement
    and closure dates.
    """
    await export_capacity_history_json()


# cms tasks from webhooks


async def task_refresh_from_cms(ctx) -> None:
    """Update a unit from the CMS"""
    pass

    await update_database_facilities_from_cms(send_slack=False)


# other tasks


async def task_clean_tmp_dir(ctx) -> None:
    """Clean the tmp dir"""
    clean_tmp_dir()


async def task_run_market_notice_update(ctx):
    await run_market_notice_update()


async def task_send_cms_updates_slack_report(ctx):
    """Send the CMS updates slack report"""
    await send_cms_updates_slack_report()


async def task_catchup_check(ctx) -> None:
    """Check for data gaps and trigger catchup processes if needed"""
    await run_catchup_check(max_gap_minutes=settings.catchup_max_gap_minutes)


async def task_catchup_days(ctx) -> None:
    """Run a catchup for the last 24 hours"""
    await catchup_last_days(days=1)


async def task_catchup_aggregates(ctx) -> None:
    """Backfill ClickHouse aggregates (market_summary and unit_intervals) for last 12h.

    Runs every 2h to fill gaps caused by timing race conditions where the scheduled
    aggregate runs before PostgreSQL has the crawled data.
    """
    await catchup_aggregates(days=0.5)


async def task_update_milestones(ctx: dict) -> None:
    """
    Incremental milestone check — runs every 5 min.

    Loads current state, queries latest completed periods from ClickHouse,
    compares against current records, and INSERTs only new records.
    """
    if not settings.run_milestones:
        return

    from opennem.recordreactor.incremental import run_incremental_milestone_check

    await run_incremental_milestone_check(alert_slack=True)


async def task_milestone_reconciliation(ctx: dict) -> None:
    """
    Monthly full reconciliation — fills any gaps from incremental detection.

    Runs backlog analysis over the last 2 years without deleting existing records.
    """
    if not settings.run_milestones:
        return

    from opennem.recordreactor.backlog import run_milestone_reconciliation

    await run_milestone_reconciliation()


async def task_check_unsplit_batteries(ctx: dict) -> None:
    """Task to check for any battery units that haven't been split into charge/discharge units.

    This task runs daily at 10am and alerts via Slack if any unsplit battery units are found.

    Args:
        ctx (dict): Task context
    """
    try:
        await check_unsplit_batteries()
    except Exception as e:
        logger.error(f"Error checking unsplit batteries: {str(e)}")
        raise


async def task_optimize_clickhouse_tables(ctx: dict) -> None:
    """
    Optimize the unit_intervals and market_summary tables to force merges and deduplication.
    This should be run periodically (e.g., daily) during low-traffic periods.
    """
    await optimize_clickhouse_tables()


async def task_refresh_clickhouse_mv_fast(ctx: dict) -> None:
    """2-day backfill every 5 min — keeps current day accurate."""
    from opennem.db.clickhouse_materialized_views import refresh_all_materialized_views

    await asyncio.to_thread(refresh_all_materialized_views, days=2, optimize=False)


async def task_refresh_clickhouse_mv_full(ctx: dict) -> None:
    """7-day backfill every 6h — wider backfill window for consistency."""
    from opennem.db.clickhouse_materialized_views import refresh_all_materialized_views

    await asyncio.to_thread(refresh_all_materialized_views, days=7, optimize=False)


async def task_weekly_summary(ctx: dict) -> None:
    """Generate weekly summary for NEM and WEM, post to Slack for approval.

    Runs Monday 7am AEST.
    """
    await run_weekly_summary(network=NetworkNEM)
    await run_weekly_summary(network=NetworkWEM)


if __name__ == "__main__":
    asyncio.run(task_nem_interval_check(ctx={"job_try": 0}))
