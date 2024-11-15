"""OpenNEM tasks"""

import asyncio
import logging

from opennem.aggregates.facility_interval import run_update_facility_intervals
from opennem.aggregates.network_demand import run_aggregates_demand_network_days
from opennem.aggregates.network_flows_v3 import run_flows_for_last_days
from opennem.api.export.tasks import export_electricitymap, export_energy, export_flows
from opennem.cms.importer import update_database_facilities_from_cms
from opennem.controllers.schema import ControllerReturn
from opennem.crawl import run_crawl
from opennem.crawlers.aemo_market_notice import run_market_notice_update
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
from opennem.exporter.facilities import export_facilities_static
from opennem.exporter.historic import export_historic_intervals
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkAU, NetworkNEM, NetworkWEM
from opennem.tasks.exceptions import OpenNEMPipelineRetryTask
from opennem.workers.energy import process_energy_from_now
from opennem.workers.facility_data_seen import update_facility_seen_range
from opennem.workers.facility_first_seen import facility_first_seen_check
from opennem.workers.system import clean_tmp_dir

logger = logging.getLogger("opennem.pipelines.nem")


async def task_nem_interval_check(ctx) -> None:
    """This task runs per interval and checks for new data"""
    _ = await run_crawl(AEMONemwebDispatchIS, latest=True)
    dispatch_scada = await run_crawl(AEMONNemwebDispatchScada, latest=True)
    _ = await run_crawl(AEMONemwebTradingIS, latest=True)

    if not dispatch_scada.inserted_records:
        logger.warning("No new data from crawlers")
        raise OpenNEMPipelineRetryTask()

    # update energy
    await process_energy_from_now(hours=1)

    # update facility aggregates
    await run_update_facility_intervals(hours=1)

    # run flows
    run_flows_for_last_days(days=1, network=NetworkNEM)

    await asyncio.gather(
        run_export_power_latest_for_network(network=NetworkNEM), run_export_power_latest_for_network(network=NetworkAU)
    )


async def task_nem_rooftop_crawl(ctx) -> None:
    """Runs the NEM rooftop crawler every rooftop interval (30 min)"""

    tasks = [
        run_crawl(AEMONemwebRooftop),
        run_crawl(AEMONemwebRooftopForecast),
    ]

    rooftop = await asyncio.gather(*tasks)

    if not rooftop or not any(r.inserted_records for r in rooftop if r):
        raise OpenNEMPipelineRetryTask()


async def task_wem_interval_check(ctx) -> None:
    """This task runs per interval and checks for new data"""
    await run_all_wem_crawlers()
    await run_export_power_latest_for_network(network=NetworkWEM)


async def task_bom_capitals_crawl(ctx) -> None:
    """Runs the BOM Capitals crawler every 10 minutes"""
    await run_crawl(BOMCapitals)


async def task_run_energy_calculation(ctx) -> None:
    """Runs the energy calculation for the last 2 hours"""
    await process_energy_from_now(hours=1)


async def task_nem_power_exports(ctx) -> None:
    """Runs the NEM exports"""
    await asyncio.gather(
        run_export_power_latest_for_network(network=NetworkNEM),
        run_export_power_latest_for_network(network=NetworkAU),
        # run_export_power_latest_for_network(network=NetworkWEMDE),
    )


async def task_export_flows(ctx) -> None:
    """Runs the flows export"""
    await export_electricitymap()
    await export_flows()


# Output and processing tasks


async def task_export_energy(ctx) -> None:
    """Runs the energy export"""
    await export_energy(latest=True)


async def task_run_flows_for_last_days(ctx) -> None:
    """Runs the flows for the last 2 days"""
    run_flows_for_last_days(days=2, network=NetworkNEM)


async def task_update_facility_aggregates_chunked(ctx) -> None:
    """Updates facility aggregates in chunks"""

    await run_update_facility_intervals(hours=4)


async def task_run_aggregates_demand_network_days(ctx) -> None:
    """Runs the demand aggregates for the last 14 days"""
    await run_aggregates_demand_network_days(days=2)


async def task_facility_first_seen_check(ctx) -> None:
    """Runs the facility first seen check"""
    await facility_first_seen_check()


async def task_export_facility_geojson(ctx) -> None:
    """Exports the facility geojson"""
    await export_facilities_static()


async def task_update_facility_seen_range(ctx) -> None:
    """Updates the facility seen range"""
    await update_facility_seen_range(interval_window_days=1)


async def task_nem_per_day_check(ctx) -> ControllerReturn:
    """This task is run daily for NEM"""
    dispatch_actuals = await run_crawl(AEMONEMDispatchActualGEN)
    await run_crawl(AEMONEMNextDayDispatch)

    if not dispatch_actuals or not dispatch_actuals.inserted_records:
        raise OpenNEMPipelineRetryTask()

    # await daily_runner()

    # export historic intervals
    for network in [NetworkNEM, NetworkWEM]:
        export_historic_intervals(limit=2, networks=[network])

    return ControllerReturn(
        server_latest=dispatch_actuals.server_latest,
        last_modified=None,
    )


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
