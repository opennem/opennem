""" OpenNEM NEM processing pipeline


All the processing pipelines for the NEM network
"""
import logging

from opennem.controllers.schema import ControllerReturn
from opennem.core.profiler import profile_task
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
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkAU, NetworkNEM
from opennem.settings import IS_DEV, settings  # noqa: F401
from opennem.workers.daily import daily_runner

logger = logging.getLogger("opennem.pipelines.nem")


class NemPipelineNoNewData(Exception):
    """ """

    pass


# Crawler tasks


def nem_dispatch_is_crawl() -> ControllerReturn:
    cr = run_crawl(AEMONemwebDispatchIS)

    if not cr or not cr.inserted_records:
        raise NemPipelineNoNewData("No new dispatch is data")


def nem_trading_is_crawl() -> None:
    cr = run_crawl(AEMONemwebTradingIS)

    if not cr or not cr.inserted_records:
        raise NemPipelineNoNewData("No new dispatch is data")


@profile_task(
    send_slack=True,
    message_fmt=(
        "`NEM`: per_interval pipeline processed"
        " `{run_task_output.inserted_records}` new records for interval `{run_task_output.server_latest}`"
    ),
)
def nem_dispatch_scada_crawl() -> ControllerReturn:
    """This task runs per interval and checks for new data"""
    dispatch_scada = run_crawl(AEMONNemwebDispatchScada)

    if not dispatch_scada or not dispatch_scada.inserted_records:
        raise NemPipelineNoNewData("No new dispatch scada data")

    run_export_power_latest_for_network(network=NetworkNEM)
    run_export_power_latest_for_network(network=NetworkAU)

    return dispatch_scada


def nem_rooftop_crawl() -> None:
    """Runs the NEM rooftop crawler every rooftop interval (30 min)"""
    rooftop = run_crawl(AEMONemwebRooftop)
    _ = run_crawl(AEMONemwebRooftopForecast)

    if not rooftop or not rooftop.inserted_records:
        raise NemPipelineNoNewData("No new rooftop data")

    run_export_power_latest_for_network(network=NetworkNEM)
    run_export_power_latest_for_network(network=NetworkAU)


@profile_task(
    send_slack=True,
    message_fmt=(
        "`NEM`: overnight pipeline processed"
        " `{run_task_output.inserted_records}` new records for day `{run_task_output.server_latest.date()}`"
    ),
)
def nem_per_day_check() -> ControllerReturn:
    """This task is run daily for NEM"""
    dispatch_actuals = run_crawl(AEMONEMDispatchActualGEN)
    dispatch_gen = run_crawl(AEMONEMNextDayDispatch)

    if not dispatch_actuals or not dispatch_actuals.inserted_records:
        raise NemPipelineNoNewData("No new dispatch actuals data")

    if (dispatch_actuals and dispatch_actuals.inserted_records) or (dispatch_gen and dispatch_gen.inserted_records):
        total_records = dispatch_actuals.inserted_records if dispatch_actuals and dispatch_actuals.inserted_records else 0
        total_records += dispatch_gen.inserted_records if dispatch_gen and dispatch_gen.inserted_records else 0

        daily_runner()

        return ControllerReturn(
            server_latest=dispatch_actuals.server_latest, total_records=total_records, inserted_records=total_records
        )

    raise NemPipelineNoNewData("No new dispatch actuals data")
