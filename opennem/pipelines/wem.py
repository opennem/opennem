""" WEM pipelines """
import logging

from opennem.core.profiler import profile_task
from opennem.crawl import run_crawl
from opennem.crawlers.apvi import APVIRooftopLatestCrawler
from opennem.crawlers.wemde import run_all_wem_crawlers
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkWEM

logger = logging.getLogger("opennem.pipelines.wem")


@profile_task(
    send_slack=True,
    message_fmt=(
        "`WEM`: per_interval pipeline processed"
        " `{run_task_output.inserted_records}` new records for interval `{run_task_output.server_latest}`"
    ),
)
def wem_per_interval_check() -> None:
    """This task runs per interval and checks for new data"""
    _ = run_crawl(APVIRooftopLatestCrawler)

    run_all_wem_crawlers()
    run_export_power_latest_for_network(network=NetworkWEM)


if __name__ == "__main__":
    wem_per_interval_check()
