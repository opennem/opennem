"""OpenNEM NEM processing pipeline


All the processing pipelines for the NEM network
"""

import asyncio
import logging

from huey.exceptions import RetryTask

from opennem import settings
from opennem.aggregates.network_flows import run_flow_update_for_interval
from opennem.aggregates.network_flows_v3 import run_flows_for_last_intervals
from opennem.controllers.schema import ControllerReturn
from opennem.crawl import run_crawl
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
from opennem.workers.daily import daily_runner

logger = logging.getLogger("opennem.pipelines.nem")


class NemPipelineNoNewData(Exception):
    """ """

    pass


# Crawler tasks
async def nem_dispatch_is_crawl() -> None:
    """Runs the dispatch_is crawl"""
    dispatch_is = await run_crawl(AEMONemwebDispatchIS)

    if not dispatch_is or not dispatch_is.inserted_records:
        raise RetryTask("No new dispatch is data")

    if dispatch_is and dispatch_is.crawls_run:
        # switch between v3 and v2 for flows here
        if settings.flows_and_emissions_v3:
            run_flows_for_last_intervals(interval_number=2, network=NetworkNEM)
        else:
            # run old flows
            run_flow_update_for_interval(interval=dispatch_is.server_latest, network=NetworkNEM)


async def nem_trading_is_crawl() -> None:
    """Runs the trading_is crawl"""
    cr = await run_crawl(AEMONemwebTradingIS)

    if not cr or not cr.inserted_records:
        raise RetryTask("No new dispatch is data")


async def nem_dispatch_scada_crawl() -> ControllerReturn:
    """This task runs per interval and checks for new data"""
    dispatch_scada = await run_crawl(AEMONNemwebDispatchScada)

    if not dispatch_scada or not dispatch_scada.inserted_records:
        raise RetryTask("No new dispatch scada data")

    await run_export_power_latest_for_network(network=NetworkNEM)
    await run_export_power_latest_for_network(network=NetworkAU)

    return dispatch_scada


async def nem_rooftop_crawl() -> None:
    """Runs the NEM rooftop crawler every rooftop interval (30 min)"""
    rooftop = await run_crawl(AEMONemwebRooftop)
    _ = await run_crawl(AEMONemwebRooftopForecast)

    if not rooftop or not rooftop.inserted_records:
        raise RetryTask("No new rooftop data")

    await run_export_power_latest_for_network(network=NetworkNEM)
    await run_export_power_latest_for_network(network=NetworkAU)


# Output and processing tasks


async def nem_per_day_check(always_run: bool = False) -> ControllerReturn:
    """This task is run daily for NEM"""
    dispatch_actuals = run_crawl(AEMONEMDispatchActualGEN)
    await run_crawl(AEMONEMNextDayDispatch)

    if not always_run or not dispatch_actuals or not dispatch_actuals.inserted_records:
        raise RetryTask("No new dispatch actuals data")

    await daily_runner()

    # export historic intervals
    for network in [NetworkNEM, NetworkWEM]:
        export_historic_intervals(limit=2, networks=[network])

    return ControllerReturn(
        server_latest=dispatch_actuals.server_latest,
        last_modified=None,
    )


if __name__ == "__main__":
    asyncio.run(nem_rooftop_crawl())
