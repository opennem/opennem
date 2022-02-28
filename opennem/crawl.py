"""Primary OpenNEM crawler

"""
import inspect
import logging
from typing import List, Optional

from pydantic import ValidationError

from opennem import settings
from opennem.controllers.schema import ControllerReturn
from opennem.core.crawlers.meta import CrawlStatTypes, crawler_get_all_meta, crawler_set_meta
from opennem.core.crawlers.schema import (
    CrawlerDefinition,
    CrawlerPriority,
    CrawlerSchedule,
    CrawlerSet,
)
from opennem.crawlers.aemo import run_aemo_mms_crawl
from opennem.crawlers.apvi import crawl_apvi_forecasts
from opennem.crawlers.wem import (
    run_wem_balancing_crawl,
    run_wem_facility_scada_crawl,
    run_wem_live_balancing_crawl,
    run_wem_live_facility_scada_crawl,
)
from opennem.utils.dates import get_today_opennem
from opennem.utils.modules import load_all_crawler_definitions

logger = logging.getLogger("opennem.crawler")


def iter_crawler_definitions(module: str):
    """Return an iterator over all spider classes defined in the given module
    that can be instantiated (i.e. which have name)
    """

    for obj in vars(module).values():
        if (
            inspect.isclass(obj)
            and issubclass(obj, CrawlerDefinition)
            and obj.__module__ == module.__name__
            and getattr(obj, "name", None)
        ):
            yield obj


def load_crawlers() -> CrawlerSet:
    """Loads all the crawler definitions from a module and returns a CrawlSet"""
    crawlers = []
    crawler_definitions = []

    if settings.crawlers_module:
        # search_modules.append()
        crawler_definitions = load_all_crawler_definitions(settings.crawlers_module)

    for crawler_inst in crawler_definitions:

        _meta = crawler_get_all_meta(crawler_inst.name)

        if not _meta:
            crawlers.append(crawler_inst)
            continue

        crawler_updated_with_meta: Optional[CrawlerDefinition] = None

        try:
            crawler_field_values = {
                **crawler_inst.dict(),
                **_meta,
                "version": "2",
            }
            crawler_updated_with_meta = CrawlerDefinition(
                **crawler_field_values,
            )
        except ValidationError as e:
            logger.error("Validation error for crawler {}: {}".format(crawler_inst.name, e))
            raise Exception("Crawler initiation error")

        if crawler_updated_with_meta:
            crawlers.append(crawler_updated_with_meta)

    cs = CrawlerSet(crawlers=crawlers)

    logger.debug(
        "Loaded {} crawlers: {}".format(len(cs.crawlers), ", ".join([i.name for i in cs.crawlers]))
    )

    return cs


def run_crawl(crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False) -> None:
    """Runs a crawl from the crawl definition with ability to overwrite last crawled and obey the defined
    limit"""

    logger.info(
        "Crawling: {}. Last Crawled: {}. Limit: {}. Last crawled: {}".format(
            crawler.name, crawler.last_crawled, crawler.limit, crawler.server_latest
        )
    )

    # now in opennem time which is Australia/Sydney
    now_opennem_time = get_today_opennem()

    crawler_set_meta(crawler.name, CrawlStatTypes.version, crawler.version)
    crawler_set_meta(crawler.name, CrawlStatTypes.last_crawled, now_opennem_time)

    cr: Optional[ControllerReturn] = crawler.processor(
        crawler=crawler, last_crawled=last_crawled, limit=crawler.limit
    )

    if not cr:
        return None

    # run here
    has_errors = False

    logger.info("Inserted {} of {} records".format(cr.inserted_records, cr.total_records))

    if cr.errors > 0:
        has_errors = True
        logger.error("Crawl controller error for {}: {}".format(crawler.name, cr.error_detail))

    if not has_errors:
        # get the time again so we can measure deltas
        crawler.last_processed = get_today_opennem()

        crawler_set_meta(crawler.name, CrawlStatTypes.latest_processed, crawler.last_processed)

        if cr.server_latest:
            crawler_set_meta(crawler.name, CrawlStatTypes.server_latest, cr.server_latest)
        else:
            logger.debug("{} has no server_latest return".format(crawler.name))

        logger.info(
            "Set last_processed to {} and server_latest to {}".format(
                crawler.last_processed, cr.server_latest
            )
        )


_CRAWLER_SET = load_crawlers()


def run_crawls_all(last_crawled: bool = True) -> None:
    """Runs all the crawl definitions"""
    if not _CRAWLER_SET.crawlers:
        raise Exception("No crawlers found")

    for crawler in _CRAWLER_SET.crawlers:
        try:
            run_crawl(crawler, last_crawled=last_crawled)
        except Exception as e:
            logger.error("Error running crawl {}: {}".format(crawler.name, e))


def run_crawls_by_schedule(schedule: CrawlerSchedule, last_crawled: bool = True) -> None:
    """Gets the crawlers by schedule and runs them"""
    if not _CRAWLER_SET.crawlers:
        raise Exception("No crawlers found")

    for crawler in _CRAWLER_SET.get_crawlers_by_schedule(schedule):
        try:
            run_crawl(crawler, last_crawled=last_crawled)
        except Exception as e:
            logger.error("Error running crawl {}: {}".format(crawler.name, e))


def get_crawler_names() -> List[str]:
    """Get a list of crawler names"""
    crawler_names: List[str] = [i.name for i in _CRAWLER_SET.crawlers]

    return crawler_names


def get_crawl_set() -> CrawlerSet:
    """Access method for crawler set"""
    return _CRAWLER_SET


if __name__ == "__main__":
    cs = get_crawl_set()

    for c in cs.crawlers:
        print(c.name)
