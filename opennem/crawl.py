"""Primary OpenNEM crawler

"""
import logging
from datetime import datetime
from typing import List

import pytz

from opennem.core.crawlers.meta import CrawlStatTypes, crawler_get_all_meta, crawler_set_meta
from opennem.crawlers.aemo import run_aemo_mms_crawl
from opennem.crawlers.apvi import crawl_apvi_forecasts
from opennem.crawlers.bom import crawl_bom_capitals
from opennem.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule, CrawlerSet
from opennem.crawlers.wem import (
    run_wem_balancing_crawl,
    run_wem_facility_scada_crawl,
    run_wem_live_balancing_crawl,
    run_wem_live_facility_scada_crawl,
)
from opennem.utils.dates import chop_datetime_microseconds

logger = logging.getLogger("opennem.crawler")


def load_crawlers() -> CrawlerSet:
    """Loads all the crawler definitions from a module and returns a CrawlSet"""
    _crawlers = []

    for i in globals():
        if isinstance(globals()[i], CrawlerDefinition):
            _crawler_inst = globals()[i]

            logger.debug("Found crawler definition: {}".format(i))

            _meta = crawler_get_all_meta(_crawler_inst.name)

            if not _meta:
                _crawlers.append(_crawler_inst)
                continue

            crawler_updated_with_meta = CrawlerDefinition(
                **{
                    **_crawler_inst.dict(),
                    **_meta,
                }
            )

            _crawlers.append(crawler_updated_with_meta)

    cs = CrawlerSet(crawlers=_crawlers)

    logger.debug("Loaded {} crawlers".format(len(cs.crawlers)))

    return cs


def run_crawl(crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False) -> None:
    logger.info(
        "Crawling: {}. Latest: {}. Limit: {}. Last crawled: {}".format(
            crawler.name, last_crawled, limit, crawler.last_crawled
        )
    )

    cr = crawler.processor(crawler=crawler, last_crawled=last_crawled, limit=limit)

    if not cr:
        return None

    # run here
    has_errors = False

    logger.info("Inserted {} of {} records".format(cr.inserted_records, cr.total_records))

    if cr.errors > 0:
        has_errors = True
        logger.error("Crawl controller error for {}: {}".format(crawler.name, cr.error_detail))

    if not has_errors:
        crawler.last_crawled = cr.last_modified
        crawler.last_processed = chop_datetime_microseconds(
            datetime.now().astimezone(pytz.timezone("Australia/Sydney"))
        )

        crawler_set_meta(crawler.name, CrawlStatTypes.last_crawled, crawler.last_crawled)
        crawler_set_meta(crawler.name, CrawlStatTypes.latest_processed, crawler.last_processed)

        logger.info("Set last updated to {}".format(cr.last_modified))


AEMONemTradingISLatest = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.current.trading_is",
    url="http://nemweb.com.au/Reports/Current/TradingIS_Reports/",
    limit=3,
    processor=run_aemo_mms_crawl,
)

AEMONemDispatchISLatest = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.current.dispatch_is",
    url="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/",
    limit=3,
    processor=run_aemo_mms_crawl,
)

AEMONEMDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/",
    limit=3,
    processor=run_aemo_mms_crawl,
)

AEMONEMDispatchActualGEN = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    name="au.nem.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/",
    limit=1,
    processor=run_aemo_mms_crawl,
)

AEMONEMNextDayDispatch = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="au.nem.dispatch",
    url="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/",
    limit=1,
    processor=run_aemo_mms_crawl,
)

AEMONEMRooftop = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.frequent,
    name="au.nem.rooftop",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/",
    limit=1,
    filename_filter=".*_MEASUREMENT_.*",
    processor=run_aemo_mms_crawl,
)


AEMONEMRooftopForecast = CrawlerDefinition(
    priority=CrawlerPriority.low,
    schedule=CrawlerSchedule.frequent,
    name="au.nem.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/",
    limit=1,
    processor=run_aemo_mms_crawl,
)

BOMCapitals = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.frequent,
    name="au.bom.capitals",
    url="none",
    limit=1,
    processor=crawl_bom_capitals,
)

APVIRooftopCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.frequent,
    name="apvi.data",
    url="none",
    processor=crawl_apvi_forecasts,
)

WEMBalancing = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.hourly,
    name="au.wem.balancing",
    processor=run_wem_balancing_crawl,
)

WEMFacilityScada = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.hourly,
    name="au.wem.facility_scada",
    processor=run_wem_facility_scada_crawl,
)

WEMBalancingLive = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.frequent,
    name="au.wem.live.balancing",
    processor=run_wem_live_balancing_crawl,
)

WEMFacilityScadaLive = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.frequent,
    name="au.wem.live.facility_scada",
    processor=run_wem_live_facility_scada_crawl,
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
    for crawler in _CRAWLER_SET.crawlers:
        logger.info(crawler.name)
