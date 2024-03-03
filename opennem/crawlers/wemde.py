"""Crawls and parses new WEMDE format"""

import logging
from datetime import datetime

from opennem.clients.wemde import wemde_parse_facilityscada, wemde_parse_trading_price
from opennem.controllers.nem import ControllerReturn
from opennem.core.crawlers.meta import CrawlStatTypes, crawler_get_meta, crawler_set_meta
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.dirlisting import get_dirlisting
from opennem.persistence.postgres_facility_scada import persist_facility_scada_bulk
from opennem.persistence.schema import SchemaBalancingSummary, SchemaFacilityScada
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.crawlers.wemde")


def run_wemde_crawl(
    crawler: CrawlerDefinition, latest: bool = True, limit: int | None = None, backfill_days: int | None = None
) -> ControllerReturn:
    logger.info("Starting WEMDE crawl")

    entries_to_fetch: list = []

    if not crawler.url and not crawler.urls:
        raise Exception("Require a URL to run AEMO WEMDE crawlers")

    if not crawler.url:
        raise Exception("Require a URL to run AEMO WEMDE crawlers")

    if not crawler.parser:
        raise Exception("Require a parser to run AEMO WEMDE crawlers")

    if not backfill_days:
        backfill_days = 365

    try:
        dirlisting = get_dirlisting(crawler.url, timezone=crawler.network.timezone if crawler.network else None)
    except Exception as e:
        raise Exception(f"Could not fetch directory listing: {crawler.url}. {e}") from e

    if crawler.filename_filter:
        dirlisting.apply_filter(crawler.filename_filter)

        logger.debug(
            f"Got {dirlisting.count} entries, {dirlisting.file_count} files and {dirlisting.directory_count} directories"
        )

    if limit:
        logger.debug(f"Limiting to {limit} files")
        entries_to_fetch = dirlisting.get_most_recent_files(limit=limit)

    elif latest:
        last_crawled = crawler_get_meta(crawler.name, CrawlStatTypes.server_latest)

        logger.debug(f"Running latest and last crawled: {last_crawled}")

        if last_crawled and isinstance(last_crawled, datetime):
            logger.debug(f"Getting files modified since {last_crawled}")
            entries_to_fetch = dirlisting.get_files_modified_since(last_crawled)
        else:
            logger.debug(f"Getting all {len(dirlisting.entries)} entries")
            entries_to_fetch = dirlisting.get_files()

    else:
        logger.debug(f"Getting all {len(dirlisting.entries)} entries")
        entries_to_fetch = dirlisting.get_files()

    if not entries_to_fetch:
        raise Exception(f"No entries to fetch for crawler {crawler.name}")

    logger.info(f"Fetching {latest=} {len(entries_to_fetch)} entries")

    latest_interval: datetime | None = None
    latest_aemo_interval_date: datetime | None = None

    data: list[SchemaFacilityScada | SchemaBalancingSummary] = []

    for entry in entries_to_fetch:
        logger.info(f"Fetching {entry.link}")

        if entry.aemo_interval_date and (not latest_aemo_interval_date or entry.aemo_interval_date > latest_aemo_interval_date):
            latest_aemo_interval_date = entry.aemo_interval_date

        try:
            data += crawler.parser(entry.link)

        except Exception as e:
            logger.error(f"Error parsing data: {e}")
            continue

    # persist data
    update_fields = ["generated", "eoi_quantity"]

    if crawler.parser == wemde_parse_trading_price:
        update_fields = ["price", "price_dispatch"]

    persist_facility_scada_bulk(records=data, update_fields=update_fields)

    logger.info(f"Persisted {len(data)} records")

    # track latest interal and update metadata
    recent_latest_interval = max([i.trading_interval for i in data if i.trading_interval])

    if recent_latest_interval and (not latest_interval or recent_latest_interval > latest_interval):
        latest_interval = recent_latest_interval

    logger.debug(f"Latest interval: {latest_interval} for {crawler.name} and {len(data)} records")

    if latest_interval:
        crawler_set_meta(crawler.name, CrawlStatTypes.latest_interval, latest_interval)

    if latest_aemo_interval_date:
        crawler_set_meta(crawler.name, CrawlStatTypes.server_latest, latest_aemo_interval_date)

    crawler_set_meta(crawler.name, CrawlStatTypes.last_crawled, get_today_opennem())

    return ControllerReturn(status=200, count=len(entries_to_fetch))


def run_all_wem_crawlers(latest: bool = True) -> None:
    for crawler in [
        AEMOWEMDETradingReport,
        AEMOWEMDEFacilityScadaHistory,
        AEMOWEMDETradingReportHistory,
    ]:
        run_wemde_crawl(crawler, latest=latest)


AEMOWEMDEFacilityScadaHistory = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.wemde.history.facility_scada",
    url="https://data.wa.aemo.com.au/public/market-data/wemde/facilityScada/previous/",
    network=NetworkWEM,
    processor=run_wemde_crawl,
    parser=wemde_parse_facilityscada,
)

AEMOWEMDETradingReportHistory = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.wemde.history.trading_report",
    url="https://data.wa.aemo.com.au/public/market-data/wemde/referenceTradingPrice/previous/",
    network=NetworkWEM,
    processor=run_wemde_crawl,
    parser=wemde_parse_trading_price,
)

AEMOWEMDETradingReport = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.wemde.current.trading_report",
    url="https://data.wa.aemo.com.au/public/market-data/wemde/referenceTradingPrice/current/",
    network=NetworkWEM,
    processor=run_wemde_crawl,
    parser=wemde_parse_trading_price,
)

if __name__ == "__main__":
    # backdate_date = datetime.fromisoformat("2024-01-12T00:00:00")
    # crawler_set_meta(AEMOWEMDEFacilityScadaHistory.name, CrawlStatTypes.server_latest, backdate_date)
    run_all_wem_crawlers(latest=False)
