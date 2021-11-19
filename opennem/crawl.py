"""Primary OpenNEM crawler

"""
import logging
import re
from datetime import datetime
from typing import List, Optional, Pattern

from pydantic import ValidationError, validator

from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.crawlers.meta import CrawlStatTypes, crawler_get_all_meta, crawler_set_meta
from opennem.core.parsers.aemo.mms import parse_aemo_urls
from opennem.core.parsers.dirlisting import DirlistingEntry, get_dirlisting
from opennem.schema.core import BaseConfig
from opennem.utils.http import http

logger = logging.getLogger("opennem.crawler")


class CrawlerDefinition(BaseConfig):
    """Defines a crawler"""

    name: str
    url: str
    limit: Optional[int]
    filename_filter: Optional[str]

    # crawl metadata
    last_crawled: Optional[datetime]
    last_processed: Optional[datetime]


class CrawlerSet(BaseConfig):
    """Defines a set of crawlers"""

    crawlers: List[CrawlerDefinition]

    def get_crawler(self, name: str) -> CrawlerDefinition:
        """Get a crawler by name"""
        _crawler_lookup = list(filter(lambda x: x.name == name, self.crawlers))

        if not _crawler_lookup:
            raise Exception(f"Could not find crawler {name}")

        return _crawler_lookup.pop()


AEMONemTradingISLatest = CrawlerDefinition(
    name="au.nem.current.trading_is",
    url="http://nemweb.com.au/Reports/Current/TradingIS_Reports/",
    limit=3,
)

AEMONemDispatchISLatest = CrawlerDefinition(
    name="au.nem.current.dispatch_is",
    url="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/",
    limit=3,
)

AEMONEMDispatchScada = CrawlerDefinition(
    name="au.nem.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/",
    limit=3,
)

AEMONEMDispatchActualGEN = CrawlerDefinition(
    name="au.nem.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/",
    limit=1,
)

AEMONEMNextDayDispatch = CrawlerDefinition(
    name="au.nem.dispatch",
    url="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/",
    limit=1,
)

AEMONEMRooftop = CrawlerDefinition(
    name="au.nem.rooftop",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/",
    limit=1,
    filename_filter=".*_MEASUREMENT_.*",
)


AEMONEMRooftopForecast = CrawlerDefinition(
    name="au.nem.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/",
    limit=1,
)


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

    controller_returns: List[ControllerReturn] = store_aemo_tableset(ts)
    has_errors = False

    for cr in controller_returns:
        logger.info("Inserted {} of {} records".format(cr.inserted_records, cr.total_records))
        if cr.errors > 0:
            has_errors = True
            logger.error("NEM Controller error for {}: {}".format(crawler.name, cr.error_detail))

    if not has_errors:
        last_modified_date = max([i.modified_date for i in entries_to_fetch])
        crawler_set_meta(crawler.name, CrawlStatTypes.last_crawled, last_modified_date)
        logger.info("Set last updated to {}".format(last_modified_date))


_CRAWLER_SET = load_crawlers()


def run_crawls_all(last_crawled: bool = True) -> None:
    for crawler in _CRAWLER_SET.crawlers:
        logger.info("Running crawl on {}".format(crawler.name))
        run_crawl(crawler, last_crawled=last_crawled)


if __name__ == "__main__":
    # crawler_set = load_crawlers()
    run_crawls_all()
