"""Crawls and parses new WEMDE format"""

import inspect
import logging
from datetime import datetime

from opennem.clients.wemde import wemde_parse_facilityscada, wemde_parse_trading_price
from opennem.controllers.nem import ControllerReturn
from opennem.core.crawlers.meta import CrawlStatTypes, crawler_get_meta, crawler_set_meta
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.aemo.filenames import AEMODataBucketSize
from opennem.core.parsers.dirlisting import get_dirlisting
from opennem.crawlers.apvi import APVIRooftopMonthCrawler
from opennem.persistence.postgres_facility_scada import persist_facility_scada_bulk
from opennem.persistence.schema import BalancingSummarySchema, FacilityScadaSchema
from opennem.schema.date_range import CrawlDateRange
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.crawlers.wemde")


async def run_wemde_crawl(
    crawler: CrawlerDefinition,
    latest: bool = True,
    limit: int | None = None,
    backfill_days: int | None = None,
    last_crawled: datetime | str | None = None,
    date_range: CrawlDateRange | None = None,
) -> ControllerReturn:
    logger.info(f"Starting WEMDE crawl with {latest=} {limit=}")

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
        dirlisting = await get_dirlisting(crawler.url, timezone=crawler.network.timezone if crawler.network else None)
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
        last_crawled = await crawler_get_meta(crawler.name, CrawlStatTypes.server_latest)

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

    data: list[FacilityScadaSchema | BalancingSummarySchema] = []

    for entry in entries_to_fetch:
        logger.info(f"Fetching {entry.link}")

        # ugh
        if isinstance(entry.aemo_interval_date, datetime) and (
            not latest_aemo_interval_date or entry.aemo_interval_date > latest_aemo_interval_date
        ):
            latest_aemo_interval_date = entry.aemo_interval_date

        try:
            if callable(crawler.parser) and inspect.iscoroutinefunction(crawler.parser):
                data += await crawler.parser(entry.link)
            else:
                data += crawler.parser(entry.link)

        except Exception as e:
            logger.error(f"Error parsing data with {crawler.parser}: {e}")
            continue

    # persist data
    update_fields = ["generated", "energy"]

    if crawler.parser == wemde_parse_trading_price:
        update_fields = ["price", "price_dispatch"]

    await persist_facility_scada_bulk(records=data, update_fields=update_fields)

    logger.info(f"Persisted {len(data)} records")

    # track latest interal and update metadata
    recent_latest_interval = max([i.interval for i in data if i.interval])

    if recent_latest_interval and (not latest_interval or recent_latest_interval > latest_interval):
        latest_interval = recent_latest_interval

    logger.debug(f"Latest interval: {latest_interval} for {crawler.name} and {len(data)} records")

    if latest_interval:
        await crawler_set_meta(crawler.name, CrawlStatTypes.latest_interval, latest_interval)

    if latest_aemo_interval_date:
        await crawler_set_meta(crawler.name, CrawlStatTypes.server_latest, latest_aemo_interval_date)

    await crawler_set_meta(crawler.name, CrawlStatTypes.last_crawled, get_today_opennem())

    cr = ControllerReturn(
        last_modified=get_today_opennem(),
        server_latest=latest_interval,
        total_records=len(data),
    )

    return cr


async def run_wemde_crawl_from_url(urls: list[str]) -> None:
    data: list[FacilityScadaSchema] = []

    for url in urls:
        data += await wemde_parse_facilityscada(url)

    await persist_facility_scada_bulk(records=data, update_fields=["generated", "energy"])


async def run_all_wem_crawlers(latest: bool = True, limit: int | None = None) -> None:
    for crawler in [
        AEMOWEMDEFacilityScada,
        AEMOWEMDETradingReport,
        AEMOWEMDEFacilityScadaHistory,
        AEMOWEMDETradingReportHistory,
    ]:
        try:
            await run_wemde_crawl(crawler, latest=latest, limit=limit)
        except Exception as e:
            logger.error(f"Error running crawler {crawler.name}: {e}")
            continue


AEMOWEMDEFacilityScadaHistory = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=365,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.wemde.history.facility_scada",
    url="https://data.wa.aemo.com.au/public/market-data/wemde/facilityScada/previous/",
    network=NetworkWEM,
    processor=run_wemde_crawl,
    parser=wemde_parse_facilityscada,
)

AEMOWEMDEFacilityScada = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=1,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.wemde.current.facility_scada",
    url="https://data.wa.aemo.com.au/public/market-data/wemde/facilityScada/current/",
    network=NetworkWEM,
    processor=run_wemde_crawl,
    parser=wemde_parse_facilityscada,
    archive_version=AEMOWEMDEFacilityScadaHistory,
)

AEMOWEMDETradingReportHistory = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=365,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.wemde.history.trading_report",
    url="https://data.wa.aemo.com.au/public/market-data/wemde/referenceTradingPrice/previous/",
    network=NetworkWEM,
    processor=run_wemde_crawl,
    parser=wemde_parse_trading_price,
)

AEMOWEMDETradingReport = CrawlerDefinition(
    bucket_size=AEMODataBucketSize.day,
    contains_days=1,
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.live,
    name="au.wemde.current.trading_report",
    url="https://data.wa.aemo.com.au/public/market-data/wemde/referenceTradingPrice/current/",
    network=NetworkWEM,
    processor=run_wemde_crawl,
    parser=wemde_parse_trading_price,
    archive_version=AEMOWEMDETradingReportHistory,
)

ALL_WEM_CRAWLERS = [AEMOWEMDEFacilityScada, AEMOWEMDETradingReport, APVIRooftopMonthCrawler]


if __name__ == "__main__":
    # backdate_date = datetime.fromisoformat("2024-01-12T00:00:00")
    # crawler_set_meta(AEMOWEMDEFacilityScadaHistory.name, CrawlStatTypes.server_latest, backdate_date)
    import asyncio

    asyncio.run(run_wemde_crawl(AEMOWEMDEFacilityScadaHistory, latest=False))
