""" WEM pipelines """
import logging

from opennem.controllers.schema import ControllerReturn
from opennem.core.profiler import profile_task
from opennem.crawl import run_crawl
from opennem.crawlers.apvi import APVIRooftopTodayCrawler
from opennem.crawlers.wem import WEMBalancing, WEMBalancingLive, WEMFacilityScada, WEMFacilityScadaLive
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
    _ = run_crawl(APVIRooftopTodayCrawler)
    _ = run_crawl(WEMBalancingLive)
    wem_scada = run_crawl(WEMFacilityScadaLive)

    # non-live wem data
    _ = run_crawl(WEMFacilityScada)
    _ = run_crawl(WEMBalancing)

    if not wem_scada or not wem_scada.inserted_records:
        raise NemPipelineNoNewData("No WEM pipeline data")

    run_export_power_latest_for_network(network=NetworkWEM)

    return wem_scada


if __name__ == "__main__":
    wem_per_interval_check()
