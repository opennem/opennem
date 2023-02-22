""" OpenNEM NEM processing pipeline


All the processing pipelines for the NEM network
"""
import logging

from opennem.aggregates.network_flows import run_flow_update_for_interval
from opennem.api.export.tasks import export_power
from opennem.controllers.schema import ControllerReturn
from opennem.core.profiler import profile_task
from opennem.crawl import run_crawl
from opennem.crawlers.nemweb import (  # AEMONEMDispatchActualGEN,; AEMONEMNextDayDispatch,; AEMONemwebRooftopForecast,
    AEMONemwebDispatchIS,
    AEMONemwebRooftop,
    AEMONemwebTradingIS,
    AEMONNemwebDispatchScada,
)
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkAU, NetworkNEM
from opennem.settings import IS_DEV, settings  # noqa: F401

logger = logging.getLogger("opennem.pipelines.nem")


class NemPipelineNoNewData(Exception):
    """ """

    pass


@profile_task(
    send_slack=True,
    message_fmt=(
        "`NEM`: per_interval pipeline processed"
        " `{run_task_output.inserted_records}` new records for interval `{run_task_output.server_latest}`"
    ),
)
def nem_per_interval_check() -> ControllerReturn:
    """This task runs per interval and checks for new data"""
    dispatch_scada = run_crawl(AEMONNemwebDispatchScada)
    run_crawl(AEMONemwebDispatchIS)
    run_crawl(AEMONemwebTradingIS)

    if not dispatch_scada or not dispatch_scada.inserted_records:
        raise NemPipelineNoNewData("No new dispatch scada data")

    if dispatch_scada and dispatch_scada.server_latest:
        run_flow_update_for_interval(interval=dispatch_scada.server_latest, network=NetworkNEM)

    run_export_power_latest_for_network(network=NetworkNEM)
    run_export_power_latest_for_network(network=NetworkAU)

    return dispatch_scada


def nem_rooftop_crawl() -> None:
    """Runs the NEM rooftop crawler every rooftop interval (30 min)"""
    rooftop = run_crawl(AEMONemwebRooftop)

    if rooftop and rooftop.inserted_records:
        export_power(latest=True)
