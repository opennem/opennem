"""Nemweb crawlers"""

import asyncio
import logging
from datetime import datetime

from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.crawlers.history import CrawlHistoryEntry, get_crawler_missing_intervals, set_crawler_history
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.aemo.filenames import AEMODataBucketSize
from opennem.core.parsers.aemo.mms import parse_aemo_url
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized, parse_aemo_url_optimized_bulk
from opennem.core.parsers.dirlisting import DirlistingEntry, get_dirlisting
from opennem.crawlers.utils import get_time_interval_for_crawler
from opennem.schema.date_range import CrawlDateRange
from opennem.schema.network import NetworkAEMORooftop, NetworkNEM

logger = logging.getLogger("opennem.crawler.nemweb")


async def process_nemweb_entry(crawler: CrawlerDefinition, entry: DirlistingEntry, max_date: datetime) -> ControllerReturn:
    controller_return: ControllerReturn | None = None

    try:
        # @NOTE optimization - if we're dealing with a large file unzip
        # to disk and parse rather than in-memory. 100,000kb
        if crawler.bulk_insert:
            controller_return = await parse_aemo_url_optimized_bulk(entry.link, persist_to_db=True)  # type: ignore
        elif entry.file_size and entry.file_size > 100_000:
            controller_return = await parse_aemo_url_optimized(entry.link)  # type: ignore
        else:
            try:
                ts = await parse_aemo_url(entry.link)
                controller_return = await store_aemo_tableset(ts)
            except Exception as e:
                logger.error(f"Error parsing {entry.link}: {e}")
                return None
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise e
    if not isinstance(controller_return, ControllerReturn):
        raise Exception("Controller returns not a ControllerReturn")

    # don't update crawl time if it fails
    if not controller_return.inserted_records:
        logger.error(f"No records inserted for {entry.link}")
        return controller_return

    if not controller_return.last_modified or max_date > controller_return.last_modified:
        controller_return.last_modified = max_date

    if controller_return.processed_records and entry.aemo_interval_date and entry.aemo_interval_date.date:
        ch = CrawlHistoryEntry(interval=entry.aemo_interval_date.date, records=controller_return.processed_records)

        try:
            await set_crawler_history(crawler_name=crawler.name, histories=[ch])
        except Exception as e:
            logger.error(f"Error updating crawl history: {e}")

    return controller_return


async def run_nemweb_aemo_crawl(
    crawler: CrawlerDefinition,
    run_fill: bool = True,
    last_crawled: bool = True,
    limit: bool = False,
    reverse: bool = True,
    latest: bool = True,
    date_range: CrawlDateRange | None = None,
) -> ControllerReturn:
    """Runs the AEMO MMS crawlers"""
    if not crawler.url and not crawler.urls:
        raise Exception("Require a URL to run AEMO MMS crawlers")

    if not crawler.url:
        raise Exception("Require a URL to run AEMO MMS crawlers")

    try:
        dirlisting = await get_dirlisting(crawler.url, timezone="Australia/Brisbane")
    except Exception as e:
        raise Exception(f"Could not fetch directory listing: {crawler.url}. {e}") from e

    if crawler.filename_filter:
        dirlisting.apply_filter(crawler.filename_filter)

    if date_range:
        logger.info(f"Applying date range: {date_range.start} - {date_range.end}")
        dirlisting.apply_date_range(date_range)

    if limit:
        logger.info(f"Limiting to {limit}")
        dirlisting.apply_limit(limit=limit)

    logger.debug(f"Got {dirlisting.count} entries, {dirlisting.file_count} files and {dirlisting.directory_count} directories")

    if not crawler.network or not crawler.network.interval_size:
        raise Exception("Require an interval size for network for this crawler")

    entries_to_fetch: list[DirlistingEntry] = dirlisting.get_files()

    # 2 years is default backfill
    # @TODO make this dynamic based on NetworkSchema
    backfill_days = 365 * 2

    if crawler.backfill_days:
        backfill_days = crawler.backfill_days

    if latest:
        time_interval = get_time_interval_for_crawler(crawler)

        missing_intervals = await get_crawler_missing_intervals(
            crawler_name=crawler.name, days=backfill_days, interval=time_interval
        )

        logger.debug(f"Have {len(missing_intervals)} missing intervals for {crawler.name} since {time_interval}")

        if not missing_intervals:
            logger.info("Nothing to do - no missing intervals")

        entries_to_fetch = dirlisting.get_files_aemo_intervals(missing_intervals)

        if not entries_to_fetch:
            logger.info("Nothing to do - no entries to fetch after applying missing intervals")
            return ControllerReturn(inserted_records=0, processed_records=0, total_records=0)

    if not entries_to_fetch:
        logger.info("Nothing to do - no entries to fetch")
        return ControllerReturn(inserted_records=0, processed_records=0, total_records=0)

    logger.info(f"Fetching {latest=} {len(entries_to_fetch)} entries")

    controller_return = ControllerReturn(inserted_records=0, processed_records=0, total_records=0)

    if reverse:
        entries_to_fetch.reverse()

    max_date = max([i.modified_date for i in entries_to_fetch if i.modified_date])

    tasks = []
    for entry in entries_to_fetch:
        tasks.append(process_nemweb_entry(crawler=crawler, entry=entry, max_date=max_date))

        if len(tasks) >= 3:
            task_results = await asyncio.gather(*tasks)

            for task_result in task_results:
                if task_result:
                    controller_return.inserted_records += task_result.inserted_records
                    controller_return.processed_records += task_result.processed_records
                    controller_return.total_records += task_result.total_records
                else:
                    logger.error(f"No task result for {entry.link}")

            tasks = []

    # complete any remaining tasks
    if tasks:
        task_results = await asyncio.gather(*tasks)

        for task_result in task_results:
            if task_result:
                controller_return.inserted_records += task_result.inserted_records
                controller_return.processed_records += task_result.processed_records
                controller_return.total_records += task_result.total_records

    if controller_return:
        controller_return.crawls_run = len(entries_to_fetch)

    return controller_return


# archive crawlers
# these are not scheduled
# @TODO could integrate these with the above and split based on max/min date

AEMONemwebTradingISArchive = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.week,
    contains_days=365,
    priority=CrawlerPriority.high,
    active=False,
    name="au.nemweb.archive.trading_is",
    url="http://nemweb.com.au/Reports/ARCHIVE/TradingIS_Reports/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
    bulk_insert=True,
)


AEMONemwebDispatchISArchive = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=365,
    priority=CrawlerPriority.high,
    active=False,
    name="au.nemweb.archive.dispatch_is",
    url="http://nemweb.com.au/Reports/ARCHIVE/DispatchIS_Reports/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
    bulk_insert=True,
)

AEMONNemwebDispatchScadaArchive = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=365,
    priority=CrawlerPriority.high,
    active=False,
    name="au.nemweb.archive.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)

AEMONemwebRooftopArchive = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.week,
    contains_days=365,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.archive.rooftop",
    url="http://www.nemweb.com.au/Reports/ARCHIVE/ROOFTOP_PV/ACTUAL/",
    filename_filter=".*_MEASUREMENT_.*",
    network=NetworkAEMORooftop,
    backfill_days=14,
    processor=run_nemweb_aemo_crawl,
)

AEMONemwebRooftopForecastArchive = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.week,
    contains_days=365,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.archive.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/ARCHIVE/ROOFTOP_PV/FORECAST/",
    filename_filter=".*_MEASUREMENT_.*",
    network=NetworkAEMORooftop,
    backfill_days=365,
    processor=run_nemweb_aemo_crawl,
)


# Current Crawlers

# TRADING_PRICE
# TRADING_INTERCONNECTORRES
AEMONemwebTradingIS = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.interval,
    contains_days=14,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    archive_version=AEMONemwebTradingISArchive,
    name="au.nemweb.current.trading_is",
    url="http://nemweb.com.au/Reports/Current/TradingIS_Reports/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)


# DISPATCH_PRICE
# DISPATCH_REGIONSUM
# DISPATCH_INTERCONNECTORRES
AEMONemwebDispatchIS = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.interval,
    contains_days=3,
    archive_version=AEMONemwebDispatchISArchive,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.current.dispatch_is",
    url="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)

# DISPATCH_SCADA
AEMONNemwebDispatchScada = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.interval,
    contains_days=3,
    archive_version=AEMONNemwebDispatchScadaArchive,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.current.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)


AEMONemwebRooftop = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.half_hour,
    contains_days=14,
    archive_version=AEMONemwebRooftopArchive,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.current.rooftop",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/",
    filename_filter=".*_MEASUREMENT_.*",
    network=NetworkAEMORooftop,
    processor=run_nemweb_aemo_crawl,
)


AEMONemwebRooftopForecast = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.half_hour,
    contains_days=14,
    archive_version=AEMONemwebRooftopForecastArchive,
    priority=CrawlerPriority.low,
    schedule=CrawlerSchedule.four_times_a_day,
    name="au.nemweb.current.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/",
    network=NetworkAEMORooftop,
    processor=run_nemweb_aemo_crawl,
)

# next day crawlers

# METER_DATA_GEN_DUID
AEMONEMDispatchActualGENArchvie = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.month,
    contains_days=365,
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="au.nemweb.archive.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/ARCHIVE/Next_Day_Actual_Gen/",
    latest=False,
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)

AEMONEMDispatchActualGEN = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=90,
    archive_version=AEMONEMDispatchActualGENArchvie,
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.twice_a_day,
    name="au.nemweb.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/",
    latest=False,
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)

# DISPATCH_UNIT_SOLUTION
AEMONEMNextDayDispatchArchvie = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.month,
    contains_days=365,
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="au.nemweb.archive.dispatch",
    url="http://nemweb.com.au/Reports/ARCHIVE/Next_Day_Dispatch/",
    latest=False,
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)

AEMONEMNextDayDispatch = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=365,
    archive_version=AEMONEMNextDayDispatchArchvie,
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.twice_a_day,
    name="au.nemweb.dispatch",
    url="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/",
    latest=False,
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)

ALL_NEMWEB_CRAWLERS = [
    AEMONNemwebDispatchScada,
    AEMONemwebDispatchIS,
    AEMONemwebTradingIS,
    AEMONemwebRooftop,
    AEMONemwebRooftopForecast,
    AEMONEMDispatchActualGEN,
    AEMONEMNextDayDispatch,
]

if __name__ == "__main__":
    from opennem.crawl import run_crawl

    asyncio.run(run_crawl(AEMONEMNextDayDispatchArchvie, latest=False, limit=None, reverse=True))
