""" OpenNEM NEM processing pipeline


All the processing pipelines for the NEM network
"""
from opennem.aggregates.network_flows import run_flow_update_for_interval
from opennem.api.export.tasks import export_power
from opennem.clients.slack import slack_message
from opennem.core.profiler import profile_task
from opennem.crawl import run_crawl
from opennem.crawlers.nemweb import (  # AEMONEMDispatchActualGEN,; AEMONEMNextDayDispatch,; AEMONemwebRooftopForecast,
    AEMONemwebDispatchIS,
    AEMONemwebRooftop,
    AEMONemwebTradingIS,
    AEMONNemwebDispatchScada,
)
from opennem.schema.network import NetworkNEM
from opennem.settings import IS_DEV, settings  # noqa: F401


class NemPipelineNoNewData(Exception):
    """ """

    pass


@profile_task(
    send_slack=True,
    message_fmt=(
        "NEM pipeline for interval {run_task_output.server_latest} inserted"
        " {run_task_output.inserted_records} records and finished in {duration}"
    ),
)
def nem_per_interval_check() -> None:
    """This task runs per interval and checks for new data"""
    dispatch_scada = run_crawl(AEMONNemwebDispatchScada)
    dispatch_is = run_crawl(AEMONemwebDispatchIS)
    trading_is = run_crawl(AEMONemwebTradingIS)

    if (
        (dispatch_scada and dispatch_scada.inserted_records)
        or (dispatch_is and dispatch_is.inserted_records)
        or (trading_is and trading_is.inserted_records)
    ):
        if dispatch_scada and dispatch_scada.server_latest:
            run_flow_update_for_interval(interval=dispatch_scada.server_latest, network=NetworkNEM)

        export_power()

    if dispatch_scada and dispatch_scada.inserted_records:
        slack_message(
            f"[{settings.env}] New NEM dispatch data for interval `{dispatch_scada.server_latest}`"
            f" with `{dispatch_scada.inserted_records}` inserted records and updated flow tasks"
        )


def nem_rooftop_crawl() -> None:
    """Runs the NEM rooftop crawler every rooftop interval (30 min)"""
    rooftop = run_crawl(AEMONemwebRooftop)

    if rooftop and rooftop.inserted_records:
        export_power(latest=True)
