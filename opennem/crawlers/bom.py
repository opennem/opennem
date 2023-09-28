"""BoM Crawler

"""
import logging
from datetime import datetime
from time import sleep

from opennem.clients.bom import get_bom_observations
from opennem.controllers.bom import store_bom_observation_intervals
from opennem.controllers.nem import ControllerReturn
from opennem.core.bom import get_stations_priority
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.schema.date_range import CrawlDateRange

logger = logging.getLogger("opennem.crawler.bom")


def crawl_bom_capitals(
    crawler: CrawlerDefinition,
    last_crawled: bool = True,
    limit: bool = False,
    latest: bool = False,
    date_range: CrawlDateRange | None = None,
) -> ControllerReturn | None:
    bom_stations = get_stations_priority(limit=crawler.limit)

    if not bom_stations:
        logger.error("Did not return any weather stations from crawler")

    cr: ControllerReturn | None = None

    for bom_station in bom_stations:
        try:
            if not bom_station.feed_url:
                logger.error(f"Station {bom_station.code} has no feed url - skipping ")
                continue

            bom_observations = get_bom_observations(bom_station.feed_url, bom_station.code)
            cr = store_bom_observation_intervals(bom_observations)

            if crawler.backoff and crawler.backoff > 0:
                logger.info(f"Backing off for {crawler.backoff}")
                sleep(crawler.backoff)
        except Exception as e:
            logger.info(f"Bom error for station {bom_station.name}: {e}")

    if cr:
        cr.last_modified = datetime.now()
        return cr

    return None


BOMCapitals = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.live,
    name="au.bom.capitals",
    url="none",
    limit=None,
    backoff=5,
    processor=crawl_bom_capitals,
)
