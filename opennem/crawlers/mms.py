""" MMS crawler """
import logging
from datetime import datetime

from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.crawlers.history import CrawlHistoryEntry, set_crawler_history
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.aemo.filenames import AEMODataBucketSize
from opennem.core.parsers.aemo.mms import parse_aemo_url
from opennem.core.parsers.aemo.nemweb import parse_aemo_url_optimized, parse_aemo_url_optimized_bulk
from opennem.core.parsers.dirlisting import DirlistingEntry, get_dirlisting

# from opennem.crawl import run_crawl
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_complete_day_for_network, month_series

logger = logging.getLogger("opennem.crawler.nemweb")

MMS_ARCHIVE_URL_FORMAT = (
    "https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/{year}"
    "/MMSDM_{year}_{month:02}/MMSDM_Historical_Data_SQLLoader/DATA/"
)

MMS_START = datetime.fromisoformat("2009-07-01T00:00:00+10:00")
# MMS_START = datetime.fromisoformat("2019-08-01T00:00:00+10:00") # test value


class AEMOCrawlerMMSException(Exception):
    """MMS crawler exception"""

    pass


def get_mms_archive_url(year: int, month: int) -> str:
    """Get the MMS archive URL"""
    return MMS_ARCHIVE_URL_FORMAT.format(year=year, month=month)


def run_aemo_mms_crawl(
    crawler: CrawlerDefinition,
    run_fill: bool = True,
    last_crawled: bool = True,
    limit: bool = False,
    latest: bool = True,
) -> ControllerReturn | None:
    """Run the MMS crawl"""

    crawler_return: ControllerReturn | None = None

    # track how many processed
    processed = 0

    for mms_crawl_date in month_series(
        start=MMS_START,
        end=get_last_complete_day_for_network(NetworkNEM),
        reverse=True,
    ):
        if crawler.limit and crawler.limit <= processed:
            logger.info(f"Hit process limit of {crawler.limit} have processed {processed}")

            return crawler_return

        crawler.url = get_mms_archive_url(mms_crawl_date.year, mms_crawl_date.month)
        cr = process_mms_url(crawler)

        if not crawler_return:
            crawler_return = cr
        else:
            if cr and cr.inserted_records:
                crawler_return.inserted_records += cr.inserted_records

        processed += 1

    return crawler_return


def process_mms_url(crawler: CrawlerDefinition) -> ControllerReturn | None:
    logger.info(f"Crawling url: {crawler.url}")

    """Runs the AEMO MMS crawlers"""
    if not crawler.url and not crawler.urls:
        raise AEMOCrawlerMMSException("Require a URL to run AEMO MMS crawlers")

    try:
        dirlisting = get_dirlisting(crawler.url, timezone="Australia/Brisbane")
    except Exception as e:
        logger.error(f"Could not fetch directory listing: {crawler.url}. {e}")
        return None

    if crawler.filename_filter:
        dirlisting.apply_filter(crawler.filename_filter)

    logger.debug(f"Got {dirlisting.count} entries, {dirlisting.file_count} files and {dirlisting.directory_count} directories")

    entries_to_fetch: list[DirlistingEntry] = dirlisting.get_files()

    if not entries_to_fetch:
        logger.error("No entries to fetch")
        return None

    for entry in entries_to_fetch:
        try:
            # @NOTE optimization - if we're dealing with a large file unzip
            # to disk and parse rather than in-memory. 100,000kb
            if crawler.bulk_insert:
                controller_returns = parse_aemo_url_optimized_bulk(entry.link, persist_to_db=True)
            elif entry.file_size and entry.file_size > 100_000:
                controller_returns = parse_aemo_url_optimized(entry.link)
            else:
                ts = parse_aemo_url(entry.link)
                controller_returns = store_aemo_tableset(ts)

            max_date = max(i.modified_date for i in entries_to_fetch if i.modified_date)

            if not controller_returns.last_modified or max_date > controller_returns.last_modified:
                controller_returns.last_modified = max_date

            if entry.aemo_interval_date:
                ch = CrawlHistoryEntry(interval=entry.aemo_interval_date, records=controller_returns.processed_records)
                set_crawler_history(crawler_name=crawler.name, histories=[ch])

        except Exception as e:
            logger.error(f"Processing error: {e}")

    return controller_returns


AEMOMMSDispatchInterconnector = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.mms.interconnector_res",
    filename_filter=".*_DISPATCHINTERCONNECTORRES_.*",
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    # limit=1,
    processor=run_aemo_mms_crawl,
)


AEMOMMSDispatchPrice = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.mms.dispatch_price",
    filename_filter=".*_DISPATCHPRICE_.*",
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    processor=run_aemo_mms_crawl,
)


AEMOMMSDispatchRegionsum = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.mms.dispatch_regionsum",
    filename_filter=".*_DISPATCHREGIONSUM_.*",
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    processor=run_aemo_mms_crawl,
)


AEMOMMSTradingPrice = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.mms.trading_price",
    filename_filter=".*_TRADINGPRICE_.*",
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    processor=run_aemo_mms_crawl,
)


AEMOMMSTradingRegionsum = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.mms.trading_regionsum",
    filename_filter=".*_TRADINGREGIONSUM_.*",
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    processor=run_aemo_mms_crawl,
)


AEMOMMSDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.mms.dispatch_scada",
    filename_filter=".*_DISPATCH_UNIT_SCADA.*",
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    processor=run_aemo_mms_crawl,
)


AEMOMMSDispatchScada = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.mms.meterdata_gen_duid",
    filename_filter=".*_METERDATA_GEN_DUID_.*",
    network=NetworkNEM,
    bucket_size=AEMODataBucketSize.month,
    processor=run_aemo_mms_crawl,
)
