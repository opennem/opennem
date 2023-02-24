"""Primary OpenNEM crawler

"""
import logging

from pydantic import ValidationError

from opennem import settings
from opennem.controllers.schema import ControllerReturn
from opennem.core.crawlers.meta import CrawlStatTypes, crawler_get_all_meta, crawler_set_meta
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerSchedule, CrawlerSet
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized
from opennem.crawlers.apvi import (
    APVIRooftopAllCrawler,
    APVIRooftopLatestCrawler,
    APVIRooftopMonthCrawler,
    APVIRooftopTodayCrawler,
)
from opennem.crawlers.bom import BOMCapitals
from opennem.crawlers.mms import (
    AEMOMMSDispatchInterconnector,
    AEMOMMSDispatchPrice,
    AEMOMMSDispatchRegionsum,
    AEMOMMSDispatchScada,
    AEMOMMSTradingPrice,
    AEMOMMSTradingRegionsum,
)
from opennem.crawlers.nemweb import (
    AEMONEMDispatchActualGEN,
    AEMONEMDispatchActualGENArchvie,
    AEMONEMNextDayDispatch,
    AEMONEMNextDayDispatchArchvie,
    AEMONemwebDispatchIS,
    AEMONemwebDispatchISArchive,
    AEMONemwebRooftop,
    AEMONemwebRooftopForecast,
    AEMONemwebTradingIS,
    AEMONemwebTradingISArchive,
    AEMONNemwebDispatchScada,
    AEMONNemwebDispatchScadaArchive,
)
from opennem.crawlers.wem import WEMBalancing, WEMBalancingLive, WEMFacilityScada, WEMFacilityScadaLive
from opennem.utils.dates import get_today_opennem
from opennem.utils.modules import load_all_crawler_definitions

logger = logging.getLogger("opennem.crawler")


def load_crawlers(live_load: bool = False) -> CrawlerSet:
    """Loads all the crawler definitions from a module and returns a CrawlSet"""
    crawlers = []
    crawler_definitions: list[CrawlerDefinition] = []

    if settings.crawlers_module:
        if live_load:
            crawler_definitions = load_all_crawler_definitions(settings.crawlers_module)

        crawler_definitions = [
            # NEM
            AEMONEMDispatchActualGEN,
            AEMONEMNextDayDispatch,
            # NEMWEB
            AEMONemwebRooftop,
            AEMONemwebRooftopForecast,
            AEMONemwebTradingIS,
            AEMONemwebDispatchIS,
            AEMONNemwebDispatchScada,
            # NEMWEB Archive
            AEMONEMDispatchActualGENArchvie,
            AEMONEMNextDayDispatchArchvie,
            AEMONNemwebDispatchScadaArchive,
            AEMONemwebTradingISArchive,
            AEMONemwebDispatchISArchive,
            # APVI
            APVIRooftopTodayCrawler,
            APVIRooftopLatestCrawler,
            APVIRooftopMonthCrawler,
            APVIRooftopAllCrawler,
            # BOM
            BOMCapitals,
            # WEM
            WEMBalancing,
            WEMBalancingLive,
            WEMFacilityScada,
            WEMFacilityScadaLive,
            # MMS Crawlers
            AEMOMMSDispatchInterconnector,
            AEMOMMSDispatchRegionsum,
            AEMOMMSDispatchPrice,
            AEMOMMSDispatchScada,
            AEMOMMSTradingPrice,
            AEMOMMSTradingRegionsum,
        ]

    for crawler_inst in crawler_definitions:
        _meta = crawler_get_all_meta(crawler_inst.name)

        if not _meta:
            crawlers.append(crawler_inst)
            continue

        crawler_updated_with_meta: CrawlerDefinition | None = None

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
            logger.error(f"Validation error for crawler {crawler_inst.name}: {e}")
            raise Exception("Crawler initiation error")

        if crawler_updated_with_meta:
            crawlers.append(crawler_updated_with_meta)

    cs = CrawlerSet(crawlers=crawlers)

    logger.debug("Loaded {} crawlers: {}".format(len(cs.crawlers), ", ".join([i.name for i in cs.crawlers])))

    return cs


def run_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False, latest: bool = True
) -> ControllerReturn | None:
    """Runs a crawl from the crawl definition with ability to overwrite last crawled and obey the defined
    limit"""

    if not settings.run_crawlers:
        logger.info(f"Crawlers are disabled. Skipping {crawler.name}")
        return None

    logger.info(
        "Crawling: {}. (Last Crawled: {}. Limit: {}. Server latest: {})".format(
            crawler.name, crawler.last_crawled, crawler.limit, crawler.server_latest
        )
    )

    # now in opennem time which is Australia/Sydney
    now_opennem_time = get_today_opennem()

    crawler_set_meta(crawler.name, CrawlStatTypes.version, crawler.version)
    crawler_set_meta(crawler.name, CrawlStatTypes.last_crawled, now_opennem_time)

    cr: ControllerReturn | None = crawler.processor(
        crawler=crawler, last_crawled=last_crawled, limit=crawler.limit, latest=latest
    )

    if not cr:
        return None

    # run here
    has_errors = False

    logger.info(f"{crawler.name} Inserted {cr.inserted_records} of {cr.total_records} records")

    if cr.errors > 0:
        has_errors = True
        logger.error(f"Crawl controller error for {crawler.name}: {cr.error_detail}")
        return None

    if not has_errors:
        if cr.server_latest:
            crawler_set_meta(crawler.name, CrawlStatTypes.latest_processed, cr.server_latest)
            crawler_set_meta(crawler.name, CrawlStatTypes.server_latest, cr.server_latest)
        else:
            logger.debug(f"{crawler.name} has no server_latest return")

        logger.info(f"Set last_processed to {crawler.last_processed} and server_latest to {cr.server_latest}")

    return cr


def run_crawl_urls(urls: list[str]) -> None:
    """Crawl a lsit of urls
    @TODO support directories
    """

    for url in urls:
        if url.lower().endswith(".zip") or url.lower().endswith(".csv"):
            try:
                cr = parse_aemo_url_optimized(url)
                logger.info(f"Parsed {url} and got {cr.inserted_records} inserted")
            except Exception as e:
                logger.error(e)


_CRAWLER_SET: CrawlerSet | None = None


def run_crawls_all(last_crawled: bool = True) -> None:
    """Runs all the crawl definitions"""
    cs = get_crawl_set()

    for crawler in cs.crawlers:
        try:
            run_crawl(crawler, last_crawled=last_crawled)
        except Exception as e:
            logger.error(f"Error running crawl {crawler.name}: {e}")


def run_crawls_by_schedule(schedule: CrawlerSchedule, last_crawled: bool = True) -> None:
    """Gets the crawlers by schedule and runs them"""
    cs = get_crawl_set()

    for crawler in cs.get_crawlers_by_schedule(schedule):
        try:
            logger.debug(f"run_crawls_by_schedule running crawler {crawler.name}")
            run_crawl(crawler, last_crawled=last_crawled)
        except Exception as e:
            logger.error(f"Error running crawl {crawler.name}: {e}")


def get_crawler_names() -> list[str]:
    """Get a list of crawler names"""
    cs = get_crawl_set()
    return [i.name for i in cs.crawlers]


def get_crawl_set() -> CrawlerSet:
    """Access method for crawler set"""
    global _CRAWLER_SET

    if not _CRAWLER_SET:
        _CRAWLER_SET = load_crawlers()

    return _CRAWLER_SET


if __name__ == "__main__":
    run_crawls_by_schedule(CrawlerSchedule.frequent)
