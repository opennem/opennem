"""OpenNEM tasks"""

import asyncio
import logging
from datetime import timedelta

import logfire
from arq import Retry

from opennem.aggregates.facility_interval import (
    run_facility_aggregate_updates,
    run_update_facility_aggregate_last_interval,
    update_facility_aggregate_last_hours,
    update_facility_aggregates_chunked,
)
from opennem.aggregates.network_demand import run_aggregates_demand_network_days
from opennem.aggregates.network_flows_v3 import run_flows_for_last_days
from opennem.api.export.tasks import export_all_daily, export_all_monthly, export_energy, export_power
from opennem.cms.importer import update_database_facilities_from_cms
from opennem.controllers.export import run_export_energy_all, run_export_energy_for_year
from opennem.crawl import run_crawl
from opennem.crawlers.aemo_market_notice import run_market_notice_update
from opennem.crawlers.apvi import APVIRooftopMonthCrawler, APVIRooftopTodayCrawler
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
from opennem.db.views import refresh_recent_aggregates
from opennem.exporter.archive import generate_archive_dirlisting, sync_archive_exports
from opennem.exporter.facilities import export_facilities_static

# from opennem.exporter.historic import export_historic_intervals
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkAU, NetworkNEM, NetworkWEM
from opennem.utils.dates import get_last_completed_interval_for_network, get_today_opennem
from opennem.workers.energy import process_energy_last_intervals
from opennem.workers.facility_data_seen import update_facility_seen_range
from opennem.workers.facility_first_seen import facility_first_seen_check
from opennem.workers.system import clean_tmp_dir

logger = logging.getLogger("opennem.pipelines.nem")

# crawl tasks


@logfire.instrument("task_nem_interval_check")
async def task_nem_interval_check(ctx) -> None:
    """This task runs per interval and checks for new data"""
    with logfire.span("task_nem_interval_check"):
        _ = await run_crawl(AEMONemwebDispatchIS, latest=True)
        dispatch_scada = await run_crawl(AEMONNemwebDispatchScada, latest=True)
        _ = await run_crawl(AEMONemwebTradingIS, latest=True)

    if not dispatch_scada.inserted_records:
        logger.warning("No new data from crawlers")
        raise Retry(defer=ctx["job_try"] * 15)

    # update facility aggregates
    await run_update_facility_aggregate_last_interval()

    # run flows
    run_flows_for_last_days(days=1, network=NetworkNEM)

    await asyncio.gather(
        run_export_power_latest_for_network(network=NetworkNEM), run_export_power_latest_for_network(network=NetworkAU)
    )

    # update energy
    await process_energy_last_intervals(num_intervals=3)


@logfire.instrument("task_nem_per_day_check")
async def task_nem_per_day_check(ctx) -> None:
    """This task is run daily for NEM"""
    dispatch_actuals = await run_crawl(AEMONEMDispatchActualGEN)
    await run_crawl(AEMONEMNextDayDispatch)

    if not dispatch_actuals or not dispatch_actuals.inserted_records:
        raise Retry(defer=ctx["job_try"] * 15)

    await process_energy_last_intervals(num_intervals=24 * 3)

    await run_facility_aggregate_updates(lookback_days=7)


async def task_nem_rooftop_crawl(ctx) -> None:
    """Runs the NEM rooftop crawler every rooftop interval (30 min)"""

    tasks = [
        run_crawl(AEMONemwebRooftop),
        run_crawl(AEMONemwebRooftopForecast),
    ]

    rooftop = await asyncio.gather(*tasks)

    if not rooftop or not any(r.inserted_records for r in rooftop if r):
        raise Retry(defer=ctx["job_try"] * 15)


@logfire.instrument("task_wem_day_crawl")
async def task_wem_day_crawl(ctx) -> None:
    """This task runs per interval and checks for new data"""
    await run_all_wem_crawlers(latest=True, limit=3)
    await update_facility_aggregate_last_hours(hours_back=36, network=NetworkWEM)
    await run_export_power_latest_for_network(network=NetworkWEM)
    await run_export_energy_for_year(network=NetworkWEM)


@logfire.instrument("task_apvi_crawl")
async def task_apvi_crawl(ctx) -> None:
    """Runs the APVI crawler every 10 minutes"""
    await run_crawl(APVIRooftopTodayCrawler)


@logfire.instrument("task_bom_capitals_crawl")
async def task_bom_capitals_crawl(ctx) -> None:
    """Runs the BOM Capitals crawler every 10 minutes"""
    await run_crawl(BOMCapitals)


#  processing tasks


@logfire.instrument("task_run_energy_calculation")
async def task_run_energy_calculation(ctx) -> None:
    """Runs the energy calculation for the last 2 hours"""
    await process_energy_last_intervals(num_intervals=4)


@logfire.instrument("task_run_flows_for_last_days")
async def task_run_flows_for_last_days(ctx) -> None:
    """Runs the flows for the last 2 days"""
    run_flows_for_last_days(days=2, network=NetworkNEM)


@logfire.instrument("task_run_aggregates_demand_network_days")
async def task_run_aggregates_demand_network_days(ctx) -> None:
    """Runs the demand aggregates for the last 14 days"""
    await run_aggregates_demand_network_days(days=2)


@logfire.instrument("task_facility_first_seen_check")
async def task_facility_first_seen_check(ctx) -> None:
    """Runs the facility first seen check"""
    await facility_first_seen_check(send_slack=True, only_generation=True)


@logfire.instrument("task_update_facility_seen_range")
async def task_update_facility_seen_range(ctx) -> None:
    """Updates the facility seen range"""
    await update_facility_seen_range(interval_window_days=1)


# Output tasks


@logfire.instrument("task_nem_power_exports")
async def task_nem_power_exports(ctx) -> None:
    """Runs the NEM exports"""
    await asyncio.gather(
        run_export_power_latest_for_network(network=NetworkNEM),
        run_export_power_latest_for_network(network=NetworkAU),
        # run_export_power_latest_for_network(network=NetworkWEMDE),
    )


@logfire.instrument("task_export_flows")
async def task_export_flows(ctx) -> None:
    """Runs the flows export"""
    pass
    # await export_electricitymap()
    # await export_flows()


@logfire.instrument("task_export_energy")
async def task_export_energy(ctx) -> None:
    """Runs the energy export"""
    await export_energy(latest=True)

    current_date = get_today_opennem()

    # @NOTE new years day fix for energy exports - run last year and current year
    if current_date.day == 1 and current_date.month == 1:
        await run_export_energy_for_year(year=current_date.year - 1)
        await run_export_energy_for_year(year=current_date.year)

    await run_export_energy_all()


@logfire.instrument("task_export_facility_geojson")
async def task_export_facility_geojson(ctx) -> None:
    """Exports the facility geojson"""
    await export_facilities_static()


@logfire.instrument("task_sync_archive_exports")
async def task_sync_archive_exports(ctx) -> None:
    """Run and sync parquet exports to output bucket"""
    await sync_archive_exports()
    await generate_archive_dirlisting()


@logfire.instrument("task_export_daily_monthly")
async def task_export_daily_monthly(ctx) -> None:
    """Runs the daily and monthly exports"""
    await export_all_daily()
    await export_all_monthly()


# cms tasks from webhooks


@logfire.instrument("task_refresh_from_cms")
async def task_refresh_from_cms(ctx) -> None:
    """Update a unit from the CMS"""
    pass

    await update_database_facilities_from_cms(send_slack=False)


# other tasks


@logfire.instrument("task_clean_tmp_dir")
async def task_clean_tmp_dir(ctx) -> None:
    """Clean the tmp dir"""
    clean_tmp_dir()


@logfire.instrument("task_run_market_notice_update")
async def task_run_market_notice_update(ctx):
    await run_market_notice_update()


# catchup tasks


@logfire.instrument("task_catchup")
async def task_catchup(ctx) -> None:
    """Runs the catchup tasks"""
    # await run_all_wem_crawlers(latest=False, limit=30)

    crawlers = [
        AEMONEMDispatchActualGEN,
        AEMONEMNextDayDispatch,
        BOMCapitals,
        APVIRooftopMonthCrawler,
    ]
    for crawler in crawlers:
        try:
            await run_crawl(crawler, latest=False, limit=30, reverse=True)
        except Exception as e:
            logger.error(f"Error running crawler {crawler}: {e}")

    crawlers_current = [
        AEMONNemwebDispatchScada,
        AEMONemwebDispatchIS,
        AEMONemwebTradingIS,
        AEMONemwebRooftop,
        AEMONemwebRooftopForecast,
    ]
    for crawler in crawlers_current:
        try:
            await run_crawl(crawler, latest=False, limit=None, reverse=True)
        except Exception as e:
            logger.error(f"Error running crawler {crawler}: {e}")

    # processing
    # await process_energy_from_now(hours=24 * 30)
    latest_interval = get_last_completed_interval_for_network(network=NetworkNEM).replace(tzinfo=None)
    await update_facility_aggregates_chunked(
        end_date=latest_interval, start_date=latest_interval - timedelta(days=30), max_concurrent=1, chunk_days=30
    )

    try:
        run_flows_for_last_days(days=30, network=NetworkNEM)
    except Exception as e:
        logger.error(f"Error running flows: {e}")

    # exports
    await export_power()
    await run_export_energy_for_year(year=2024)
    await run_export_energy_for_year(year=2023)
    # await run_export_energy_all(network_region_code="NSW1")
    await run_export_energy_all()


async def refresh_continuous_aggregates() -> None:
    """
    Task to refresh all continuous aggregates for recent data.
    This task should be scheduled to run periodically.
    """
    await refresh_recent_aggregates()


if __name__ == "__main__":
    asyncio.run(task_catchup(ctx=None))
