"""AEMO Crawlers


"""
import logging
from typing import List, Optional

from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.aemo.mms import parse_aemo_urls
from opennem.core.parsers.dirlisting import DirlistingEntry, get_dirlisting

logger = logging.getLogger("opennem.crawler.aemo")


def run_aemo_mms_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> Optional[ControllerReturn]:
    """Runs the AEMO MMS crawlers"""
    if not crawler.url:
        raise Exception("Require a URL to run AEMO MMS crawlers")

    dirlisting = get_dirlisting(crawler.url, timezone="Australia/Brisbane")

    if crawler.filename_filter:
        dirlisting.apply_filter(crawler.filename_filter)

    logger.debug(
        "Got {} entries, {} files and {} directories".format(
            dirlisting.count, dirlisting.file_count, dirlisting.directory_count
        )
    )

    entries_to_fetch: List[DirlistingEntry] = []

    if (crawler.latest and crawler.server_latest) and last_crawled:
        entries_to_fetch = dirlisting.get_files_modified_since(crawler.server_latest)
        logger.debug("Getting last crawled since {}".format(crawler.server_latest))

    elif crawler.limit or limit:
        entries_to_fetch = dirlisting.get_most_recent_files(limit=crawler.limit)
        logger.debug("Getting limit {}".format(crawler.limit))

    else:
        entries_to_fetch = dirlisting.get_files()

    if not entries_to_fetch:
        logger.info("Nothing to do")
        return None

    logger.info("Fetching {} entries".format(len(entries_to_fetch)))

    ts = parse_aemo_urls([i.link for i in entries_to_fetch])

    controller_returns = store_aemo_tableset(ts)
    controller_returns.last_modified = max(
        [i.modified_date for i in entries_to_fetch if i.modified_date]
    )

    return controller_returns


# Trading_IS

AEMONemTradingISLatest = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.latest.trading_is",
    url="http://nemweb.com.au/Reports/Current/TradingIS_Reports/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

AEMONemTradingISCurrent = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.hourly,
    name="au.nem.current.trading_is",
    url="http://nemweb.com.au/Reports/Current/TradingIS_Reports/",
    latest=False,
    limit=12 * 24 * 7,
    processor=run_aemo_mms_crawl,
)

#  Dispatch_IS

AEMONemDispatchISLatest = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.latest.dispatch_is",
    url="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/",
    latest=True,
    processor=run_aemo_mms_crawl,
)


AEMONemDispatchISCurrent = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.hourly,
    name="au.nem.current.dispatch_is",
    url="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/",
    latest=False,
    limit=2016,
    processor=run_aemo_mms_crawl,
)

# Dispatch Scada

AEMONEMDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nem.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

AEMONEMCurrentDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.hourly,
    name="au.nem.current.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/",
    latest=False,
    # one week
    limit=2016,
    processor=run_aemo_mms_crawl,
)

AEMONEMArchiveDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.daily,
    name="au.nem.archive.latest.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/",
    latest=False,
    # 3 + 4d
    limit=4,
    processor=run_aemo_mms_crawl,
)

# Next day gens and dispatch

AEMONEMDispatchActualGEN = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.twice_a_day,
    name="au.nem.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

AEMONEMNextDayDispatch = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.twice_a_day,
    name="au.nem.dispatch",
    url="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/",
    latest=True,
    processor=run_aemo_mms_crawl,
)

# Rooftop data

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
    schedule=CrawlerSchedule.hourly,
    name="au.nem.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/",
    latest=True,
    processor=run_aemo_mms_crawl,
)
