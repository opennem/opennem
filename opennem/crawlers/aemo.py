"""AEMO Crawlers


"""
import logging
from typing import List

from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.aemo.mms import parse_aemo_urls
from opennem.core.parsers.dirlisting import DirlistingEntry, get_dirlisting

logger = logging.getLogger("opennem.crawler.aemo")


def run_aemo_mms_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn | None:
    """Runs the AEMO MMS crawlers"""
    if not crawler.url:
        raise Exception("Require a URL to run AEMO MMS crawlers")

    try:
        dirlisting = get_dirlisting(crawler.url, timezone="Australia/Brisbane")
    except Exception as e:
        logger.error(f"Could not fetch directory listing: {crawler.url}. {e}")
        return None

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
    controller_returns.last_modified = max([i.modified_date for i in entries_to_fetch if i.modified_date])

    return controller_returns


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

# AEMONEMDispatchActualGENArchive = CrawlerDefinition(
#     priority=CrawlerPriority.medium,
#     schedule=CrawlerSchedule.daily,
#     name="au.nem.catchup.dispatch_actual_gen",
#     url="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/",
#     latest=False,
#     limit=14,
#     processor=run_aemo_mms_crawl,
# )

# AEMONEMNextDayDispatchArchive = CrawlerDefinition(
#     priority=CrawlerPriority.medium,
#     schedule=CrawlerSchedule.daily,
#     name="au.nem.catchup.dispatch",
#     url="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/",
#     latest=False,
#     limit=14,
#     processor=run_aemo_mms_crawl,
# )

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

AEMONEMCurrentRooftop = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.frequent,
    name="au.nem.current.rooftop",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/",
    latest=False,
    limit=2 * 12,
    filename_filter=".*_MEASUREMENT_.*",
    processor=run_aemo_mms_crawl,
)

AEMONEMRooftopForecast = CrawlerDefinition(
    priority=CrawlerPriority.low,
    schedule=CrawlerSchedule.four_times_a_day,
    name="au.nem.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/",
    latest=True,
    processor=run_aemo_mms_crawl,
)
