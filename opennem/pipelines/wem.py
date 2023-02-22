""" WEM pipelines """
import logging

from opennem.controllers.schema import ControllerReturn
from opennem.core.profiler import profile_task
from opennem.crawl import run_crawl
from opennem.crawlers.apvi import APVIRooftopTodayCrawler
from opennem.crawlers.wem import WEMBalancingLive, WEMFacilityScadaLive
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.pipelines.nem import NemPipelineNoNewData
from opennem.schema.network import NetworkWEM
from opennem.settings import IS_DEV, settings  # noqa: F401

logger = logging.getLogger("opennem.pipelines.wem")


@profile_task(
    send_slack=True,
    message_fmt=(
        "`WEM`: per_interval pipeline processed"
        " `{run_task_output.inserted_records}` new records for interval `{run_task_output.server_latest}`"
    ),
)
def wem_per_interval_check() -> ControllerReturn:
    """This task runs per interval and checks for new data"""
    apvi = run_crawl(APVIRooftopTodayCrawler)
    wem_balancing = run_crawl(WEMBalancingLive)
    wem_scada = run_crawl(WEMFacilityScadaLive)

    if not wem_scada or not wem_scada.inserted_records:
        raise NemPipelineNoNewData("No WEM pipeline data")

    if (
        (apvi and apvi.inserted_records)
        or (wem_balancing and wem_balancing.inserted_records)
        or (wem_scada and wem_scada.inserted_records)
    ):
        run_export_power_latest_for_network(network=NetworkWEM)

        return wem_scada

    raise NemPipelineNoNewData("No WEM pipeline data")
