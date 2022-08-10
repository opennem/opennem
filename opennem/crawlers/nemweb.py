""" Nemweb crawlers """
import logging

from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.crawlers.history import CrawlHistoryEntry, get_crawler_missing_intervals, set_crawler_history
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.aemo.filenames import AEMODataBucketSize
from opennem.core.parsers.aemo.mms import parse_aemo_url
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized
from opennem.core.parsers.dirlisting import DirlistingEntry, get_dirlisting
from opennem.core.time import get_interval, get_interval_by_size
from opennem.schema.network import NetworkAEMORooftop, NetworkNEM
from opennem.schema.time import TimeInterval

logger = logging.getLogger("opennem.crawler.nemweb")


def get_time_interval_for_crawler(crawler: CrawlerDefinition) -> TimeInterval:
    """For a crawler get its interval size"""
    time_interval: TimeInterval | None = None

    if crawler.bucket_size:
        match crawler.bucket_size:
            case AEMODataBucketSize.interval:
                time_interval = get_interval_by_size(crawler.network.interval_size)
            case AEMODataBucketSize.day:
                time_interval = get_interval("1d")
            case AEMODataBucketSize.week:
                time_interval = get_interval("1w")
            case AEMODataBucketSize.fortnight:
                time_interval = get_interval("1f")
            case AEMODataBucketSize.month:
                time_interval = get_interval("1M")
            case AEMODataBucketSize.year:
                time_interval = get_interval("1Y")

    elif crawler.network and crawler.network.interval_size:
        time_interval = get_interval_by_size(crawler.network.interval_size)

    if not time_interval:
        raise Exception(f"Could not get a time interval for crawler: {crawler.network.code} {crawler.bucket_size}")

    return time_interval


def run_nemweb_aemo_crawl(
    crawler: CrawlerDefinition,
    run_fill: bool = True,
    last_crawled: bool = True,
    limit: bool = False,
    latest: bool = False,
) -> ControllerReturn | None:
    """Runs the AEMO MMS crawlers"""
    if not crawler.url and not crawler.urls:
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

    if not crawler.network or not crawler.network.interval_size:
        raise Exception("Require an interval size for network for this crawler")

    # 2 years is default backfill
    # @TODO make this dynamic based on NetworkSchema
    backfill_days = 365 * 2

    if crawler.backfill_days:
        backfill_days = crawler.backfill_days

    entries_to_fetch: list[DirlistingEntry] = dirlisting.get_files()

    if not latest:
        time_interval = get_time_interval_for_crawler(crawler)

        missing_intervals = get_crawler_missing_intervals(
            crawler_name=crawler.name, days=backfill_days, interval=time_interval
        )

        logger.debug(f"Have {len(missing_intervals)} missing intervals")

        if not missing_intervals:
            logger.info("Nothing to do")

        entries_to_fetch = dirlisting.get_files_aemo_intervals(missing_intervals)

    if not entries_to_fetch:
        logger.info("Nothing to do")
        return None

    logger.info(f"Fetching {latest=} {len(entries_to_fetch)} entries")

    for entry in entries_to_fetch:
        try:
            # @NOTE optimization - if we're dealing with a large file unzip
            # to disk and parse rather than in-memory. 100,000kb
            if entry.file_size and entry.file_size > 100_000:
                controller_returns = parse_aemo_url_optimized(entry.link)
            else:
                ts = parse_aemo_url(entry.link)
                controller_returns = store_aemo_tableset(ts)

            max_date = max([i.modified_date for i in entries_to_fetch if i.modified_date])

            if not controller_returns.last_modified or max_date > controller_returns.last_modified:
                controller_returns.last_modified = max_date

            if entry.aemo_interval_date:
                ch = CrawlHistoryEntry(interval=entry.aemo_interval_date, records=controller_returns.processed_records)
                set_crawler_history(crawler_name=crawler.name, histories=[ch])

        except Exception as e:
            logger.error(f"Processing error: {e}")

    return controller_returns


AEMONemwebTradingIS = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.trading_is",
    url="http://nemweb.com.au/Reports/Current/TradingIS_Reports/",
    network=NetworkNEM,
    backfill_days=14,
    processor=run_nemweb_aemo_crawl,
)


AEMONemwebDispatchIS = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.dispatch_is",
    url="http://nemweb.com.au/Reports/Current/DispatchIS_Reports/",
    network=NetworkNEM,
    backfill_days=2,
    processor=run_nemweb_aemo_crawl,
)

AEMONNemwebDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/",
    network=NetworkNEM,
    backfill_days=2,
    processor=run_nemweb_aemo_crawl,
)


AEMONemwebRooftop = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.nemweb.rooftop",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/",
    filename_filter=".*_MEASUREMENT_.*",
    network=NetworkAEMORooftop,
    backfill_days=14,
    processor=run_nemweb_aemo_crawl,
)


AEMONemwebRooftopForecast = CrawlerDefinition(
    priority=CrawlerPriority.low,
    schedule=CrawlerSchedule.four_times_a_day,
    name="au.nemweb.rooftop_forecast",
    url="http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/",
    latest=True,
    network=NetworkAEMORooftop,
    backfill_days=14,
    processor=run_nemweb_aemo_crawl,
)

# archive crawlers
# these are not scheduled
# @TODO could integrate these with the above and split based on max/min date

AEMONemwebTradingISArchive = CrawlerDefinition(
    priority=CrawlerPriority.high,
    active=False,
    name="au.nemweb.archive.trading_is",
    url="http://nemweb.com.au/Reports/ARCHIVE/TradingIS_Reports/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)


AEMONemwebDispatchISArchive = CrawlerDefinition(
    priority=CrawlerPriority.high,
    active=False,
    name="au.nemweb.archive.dispatch_is",
    url="http://nemweb.com.au/Reports/ARCHIVE/DispatchIS_Reports/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)

AEMONNemwebDispatchScadaArchive = CrawlerDefinition(
    priority=CrawlerPriority.high,
    active=False,
    name="au.nemweb.archive.dispatch_scada",
    url="http://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/",
    network=NetworkNEM,
    processor=run_nemweb_aemo_crawl,
)


# next day crawlers

AEMONEMDispatchActualGEN = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.twice_a_day,
    name="au.nemweb.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/",
    latest=False,
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.day,
    processor=run_nemweb_aemo_crawl,
)

AEMONEMNextDayDispatch = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.twice_a_day,
    name="au.nemweb.dispatch",
    url="http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/",
    latest=False,
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.day,
    processor=run_nemweb_aemo_crawl,
)


AEMONEMDispatchActualGENArchvie = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="au.nemweb.archive.dispatch_actual_gen",
    url="http://www.nemweb.com.au/Reports/ARCHIVE/Next_Day_Actual_Gen/",
    latest=False,
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    processor=run_nemweb_aemo_crawl,
)

AEMONEMNextDayDispatchArchvie = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="au.nemweb.archive.dispatch",
    url="http://nemweb.com.au/Reports/ARCHIVE/Next_Day_Dispatch/",
    latest=False,
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.day,
    processor=run_nemweb_aemo_crawl,
)

if __name__ == "__main__":
    pass
