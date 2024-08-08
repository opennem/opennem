"""WEM pipelines"""

import logging

from opennem.crawl import run_crawl
from opennem.crawlers.apvi import APVIRooftopLatestCrawler
from opennem.crawlers.wemde import run_all_wem_crawlers
from opennem.pipelines.export import run_export_power_latest_for_network
from opennem.schema.network import NetworkWEM

logger = logging.getLogger("opennem.pipelines.wem")


async def wem_per_interval_check() -> None:
    """This task runs per interval and checks for new data"""
    _ = await run_crawl(APVIRooftopLatestCrawler)

    await run_all_wem_crawlers()
    await run_export_power_latest_for_network(network=NetworkWEM)


if __name__ == "__main__":
    import asyncio

    asyncio.run(wem_per_interval_check())
