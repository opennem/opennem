"""Primary OpenNEM crawler

"""
import logging
from typing import List, Optional

from pydantic import ValidationError

from opennem.controllers.schema import ControllerReturn
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
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.crawler")


def load_crawlers() -> CrawlerSet:
    """Loads all the crawler definitions from a module and returns a CrawlSet"""
    _crawlers = []

    for i in globals():
        if isinstance(globals()[i], CrawlerDefinition):
            _crawler_inst = globals()[i]

            _meta = crawler_get_all_meta(_crawler_inst.name)

            if not _meta:
                _crawlers.append(_crawler_inst)
                continue

            crawler_updated_with_meta: Optional[CrawlerDefinition] = None

            try:
                crawler_field_values = {
                    **_crawler_inst.dict(),
                    **_meta,
                    "version": "2",
                }
                crawler_updated_with_meta = CrawlerDefinition(
                    **crawler_field_values,
                )
            except ValidationError as e:
                logger.error("Validation error for crawler {}: {}".format(_crawler_inst.name, e))
                raise Exception("Crawler initiation error")

            if crawler_updated_with_meta:
                _crawlers.append(crawler_updated_with_meta)

    cs = CrawlerSet(crawlers=_crawlers)

    logger.debug(
        "Loaded {} crawlers: {}".format(len(cs.crawlers), ", ".join([i.name for i in cs.crawlers]))
    )

    return cs


def run_crawl(crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False) -> None:
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
        crawler.server_latest = cr.server_latest

        crawler_set_meta(crawler.name, CrawlStatTypes.latest_processed, crawler.last_processed)

        if cr.server_latest:
            crawler_set_meta(crawler.name, CrawlStatTypes.server_latest, crawler.server_latest)
        else:
            logger.debug("{} has no server_latest return".format(crawler.name))

        logger.info(
            "Set last_proceesed to {} and server_latest to {}".format(
                crawler.last_processed, crawler.server_latest
            )
        )


AEMONemTradingISLatest = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.current.trading_is",
    url="http://nemweb.com.au/Reports/Current/TradingIS_Reports/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

AEMONemDispatchISLatest = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.current.dispatch_is",
    url="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

AEMONEMDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/",
    latest=True,
    processor=run_aemo_mms_crawl,
)


AEMONEMDispatchActualGEN = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    name="au.nem.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

AEMONEMNextDayDispatch = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="au.nem.dispatch",
    url="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

AEMONEMRooftop = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.frequent,
    name="au.nem.rooftop",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/",
    latest=True,
    filename_filter=".*_MEASUREMENT_.*",
    processor=run_aemo_mms_crawl,
)


AEMONEMRooftopForecast = CrawlerDefinition(
    priority=CrawlerPriority.low,
    schedule=CrawlerSchedule.frequent,
    name="au.nem.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

BOMCapitals = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.frequent,
    name="au.bom.capitals",
    url="none",
    limit=1,
    backoff=5,
    processor=crawl_bom_capitals,
)

APVIRooftopTodayCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.frequent,
    name="apvi.today.data",
    url="none",
    latest=True,
    processor=crawl_apvi_forecasts,
)

APVIRooftopLatestCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.four_times_a_day,
    name="apvi.latest.data",
    limit=3,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


APVIRooftopMonthCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="apvi.month.data",
    limit=30,
    url="none",
    latest=False,
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
    cs = get_crawl_set()

    for c in cs.get_crawlers_by_match("apvi"):
        run_crawl(c)
