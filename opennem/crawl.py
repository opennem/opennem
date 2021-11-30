"""Primary OpenNEM crawler

"""
import logging
from datetime import datetime
from typing import List, Optional

import pytz

from opennem.clients.bom import get_bom_observations
from opennem.controllers.bom import store_bom_observation_intervals
from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.crawlers.meta import CrawlStatTypes, crawler_get_all_meta, crawler_set_meta
from opennem.core.parsers.aemo.mms import parse_aemo_urls
from opennem.core.parsers.dirlisting import DirlistingEntry, get_dirlisting
from opennem.crawlers.apvi import crawl_apvi_forecasts
from opennem.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule, CrawlerSet
from opennem.crawlers.wem import (
    run_wem_balancing_crawl,
    run_wem_facility_scada_crawl,
    run_wem_live_balancing_crawl,
    run_wem_live_facility_scada_crawl,
)
from opennem.spiders.bom.utils import get_stations_priority

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


def run_aemo_mms_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> Optional[ControllerReturn]:
    if not crawler.url:
        raise Exception("Require a URL to run AEMO MMS crawlers")

    dirlisting = get_dirlisting(crawler.url)

    if crawler.filename_filter:
        dirlisting.apply_filter(crawler.filename_filter)

    logger.debug(
        "Got {} entries, {} files and {} directories".format(
            dirlisting.count, dirlisting.file_count, dirlisting.directory_count
        )
    )

    entries_to_fetch: List[DirlistingEntry] = []

    if last_crawled and crawler.last_crawled:
        entries_to_fetch = dirlisting.get_files_modified_since(crawler.last_crawled)

    elif limit and crawler.limit:
        entries_to_fetch = dirlisting.get_most_recent_files(limit=crawler.limit)

    else:
        entries_to_fetch = dirlisting.get_files()

    if not entries_to_fetch:
        logger.info("Nothing to do")
        return None

    logger.info("Fetching {} entries".format(len(entries_to_fetch)))

    ts = parse_aemo_urls([i.link for i in entries_to_fetch])

    controller_returns = store_aemo_tableset(ts)
    controller_returns.last_modified = max([i.modified_date for i in entries_to_fetch])  # type: ignore

    return controller_returns


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
        crawler.last_processed = datetime.now().astimezone(pytz.timezone("Australia/Sydney"))

        crawler_set_meta(crawler.name, CrawlStatTypes.last_crawled, crawler.last_crawled)
        crawler_set_meta(crawler.name, CrawlStatTypes.latest_processed, crawler.last_processed)

        logger.info("Set last updated to {}".format(cr.last_modified))


def crawl_bom_capitals(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    bom_stations = get_stations_priority()

    for bom_station in bom_stations:
        try:
            bom_observations = get_bom_observations(bom_station.feed_url, bom_station.code)
            cr = store_bom_observation_intervals(bom_observations)
        except Exception as e:
            logger.error("Bom error for station {}: {}".format(bom_station.name, e))

    cr.last_modified = datetime.now()

    return cr


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
    if not _CRAWLER_SET.crawlers:
        raise Exception("No crawlers found")

    for crawler in _CRAWLER_SET.crawlers:
        logger.info("Running crawl on {}".format(crawler.name))
        run_crawl(crawler, last_crawled=last_crawled)


def run_crawls_by_schedule(schedule: CrawlerSchedule, last_crawled: bool = True) -> None:
    if not _CRAWLER_SET.crawlers:
        raise Exception("No crawlers found")

    for crawler in _CRAWLER_SET.get_crawlers_by_schedule(schedule):
        run_crawl(crawler, last_crawled=last_crawled)


if __name__ == "__main__":
    # crawler_set = load_crawlers()
    # run_crawls_all()
    # run_crawls_by_schedule(CrawlerSchedule.frequent)
    wem = _CRAWLER_SET.get_crawlers_by_match(".wem.")
    run_crawl(_CRAWLER_SET.get_crawler("au.wem.live.balancing"))

    # for i in wem:
    # print(i.name)
    # run_crawl(i)
    # pass
