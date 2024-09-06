"""OpenNEM tasks"""

import asyncio
import logging

from opennem.aggregates.network_flows_v3 import run_flows_for_last_intervals
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
from opennem.exporter.historic import export_historic_intervals
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkAU, NetworkNEM, NetworkWEM
from opennem.tasks.exceptions import OpenNEMPipelineRetryTask
from opennem.workers.daily import daily_runner

logger = logging.getLogger("opennem.pipelines.nem")


async def task_nem_interval_check(ctx) -> None:
    """This task runs per interval and checks for new data"""
    tasks = [
        run_crawl(AEMONemwebDispatchIS, latest=True),
        run_crawl(AEMONNemwebDispatchScada, latest=True),
        run_crawl(AEMONemwebTradingIS, latest=True),
    ]

    results = await asyncio.gather(*tasks)

    if not any(r.inserted_records for r in results if r):
        raise OpenNEMPipelineRetryTask()

    # run flows
    run_flows_for_last_intervals(interval_number=2, network=NetworkNEM)

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


async def task_bom_capitals_crawl(ctx) -> None:
    """Runs the BOM Capitals crawler every 10 minutes"""
    await run_crawl(BOMCapitals)


# Output and processing tasks


async def nem_per_day_check(always_run: bool = False) -> ControllerReturn:
    """This task is run daily for NEM"""
    dispatch_actuals = run_crawl(AEMONEMDispatchActualGEN)
    await run_crawl(AEMONEMNextDayDispatch)

    if not always_run or not dispatch_actuals or not dispatch_actuals.inserted_records:
        raise OpenNEMPipelineRetryTask()

    await daily_runner()

    # export historic intervals
    for network in [NetworkNEM, NetworkWEM]:
        export_historic_intervals(limit=2, networks=[network])

    return ControllerReturn(
        server_latest=dispatch_actuals.server_latest,
        last_modified=None,
    )


# other tasks


async def task_run_market_notice_update(ctx):
    await run_market_notice_update()
