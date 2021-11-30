"""BoM Crawler

"""
import logging
from datetime import datetime

from opennem.clients.bom import get_bom_observations
from opennem.controllers.bom import store_bom_observation_intervals
from opennem.controllers.nem import ControllerReturn
from opennem.crawlers.schema import CrawlerDefinition
from opennem.spiders.bom.utils import get_stations_priority

logger = logging.getLogger("opennem.crawler.bom")


def crawl_bom_capitals(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    bom_stations = get_stations_priority()

    for bom_station in bom_stations:
        try:
            if not bom_station.feed_url:
                logger.error("Station {} has no feed url - skipping ".format(bom_station.code))
                continue

            bom_observations = get_bom_observations(bom_station.feed_url, bom_station.code)
            cr = store_bom_observation_intervals(bom_observations)
        except Exception as e:
            logger.info("Bom error for station {}: {}".format(bom_station.name, e))

    cr.last_modified = datetime.now()

    return cr
