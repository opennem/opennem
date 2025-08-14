"""APVI Rooftop Data Crawler"""

import logging
from datetime import date

from opennem.clients.apvi import APVIForecastSet, get_apvi_rooftop_data
from opennem.controllers.apvi import store_apvi_forecastset
from opennem.controllers.schema import ControllerReturn
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.schema.date_range import CrawlDateRange
from opennem.schema.network import NetworkAPVI
from opennem.utils.dates import date_series, get_today_nem

logger = logging.getLogger("opennem.crawlers.apvi")


class APVICrawlerException(Exception):
    """Specific Exception"""

    pass


async def crawl_apvi_forecasts(
    crawler: CrawlerDefinition,
    last_crawled: bool = True,
    limit: bool = False,
    latest: bool = False,
    date_range: CrawlDateRange | None = None,
) -> ControllerReturn:
    """Runs the APVI crawl definition"""
    apvi_return = ControllerReturn()

    if crawler.latest:
        return await run_apvi_crawl()

    # run the entire date range
    elif crawler.limit:
        for day_run in date_series(get_today_nem().date(), length=crawler.limit, reverse=True):
            apvi_forecast_return = await run_apvi_crawl(day_run)

            if not apvi_forecast_return:
                raise APVICrawlerException("Bad run_apvi_crawl return none or no server_latest")

            apvi_return.processed_records += apvi_forecast_return.processed_records
            apvi_return.total_records += apvi_forecast_return.total_records
            apvi_return.inserted_records += apvi_forecast_return.inserted_records
            apvi_return.errors += apvi_forecast_return.errors

            if not apvi_forecast_return.server_latest:
                logger.warn(f"Did not get server_latest from run_apvi_crawl for date {day_run}")
                continue

            if not apvi_return.server_latest or (apvi_return.server_latest < apvi_forecast_return.server_latest):
                apvi_return.server_latest = apvi_forecast_return.server_latest

    # run all
    else:
        if not NetworkAPVI.data_first_seen:
            raise Exception("Require data_first_seen for network to parse")

        for day_run in date_series(get_today_nem().date(), NetworkAPVI.data_first_seen, reverse=False):
            apvi_forecast_return = await run_apvi_crawl(day_run)

            apvi_return.processed_records += apvi_forecast_return.processed_records
            apvi_return.total_records += apvi_forecast_return.total_records
            apvi_return.inserted_records += apvi_forecast_return.inserted_records
            apvi_return.errors += apvi_forecast_return.errors

            if not apvi_forecast_return or not apvi_forecast_return.server_latest:
                raise APVICrawlerException("Bad run_apvi_crawl return none or no server_latest")

            if not apvi_return.server_latest or apvi_return.server_latest < apvi_forecast_return.server_latest:
                apvi_return.server_latest = apvi_forecast_return.server_latest

    return apvi_return


async def run_apvi_crawl(day: date | None = None) -> ControllerReturn:
    """Run the APVI crawl for a given day"""

    apvi_forecast_set: APVIForecastSet | None = None

    logger.info(f"Getting APVI data for day {day}")
    apvi_forecast_set = await get_apvi_rooftop_data(day=day)

    if not apvi_forecast_set:
        raise Exception("Could not get APVI forecast set")

    cr = await store_apvi_forecastset(apvi_forecast_set)

    # await update_apvi_facility_capacities(apvi_forecast_set)

    cr.server_latest = apvi_forecast_set.server_latest

    return cr


APVIRooftopTodayCrawler: CrawlerDefinition = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.frequent,
    contains_days=1,
    name="apvi.today.data",
    limit=2,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)

APVIRooftopLatestCrawler: CrawlerDefinition = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.four_times_a_day,
    contains_days=7,
    name="apvi.latest.data",
    limit=7,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


APVIRooftopMonthCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    contains_days=30,
    name="apvi.month.data",
    limit=45,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


APVIRooftopYearCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    contains_days=365,
    name="apvi.year.data",
    limit=365,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


APVIRooftopAllCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    contains_days=365,
    name="apvi.all.data",
    limit=None,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


if __name__ == "__main__":
    pass
