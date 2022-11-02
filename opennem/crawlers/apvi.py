"""APVI Rooftop Data Crawler

"""

import logging
from datetime import datetime

from opennem.clients.apvi import APVIForecastSet, get_apvi_rooftop_data, get_apvi_rooftop_today
from opennem.controllers.apvi import store_apvi_forecastset, update_apvi_facility_capacities
from opennem.controllers.schema import ControllerReturn
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.utils.dates import date_series, get_today_nem

logger = logging.getLogger("opennem.crawlers.apvi")

APVI_MIN_DATE = datetime.fromisoformat("2015-03-01T00:00:00+10:00")


def crawl_apvi_forecasts(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False, latest: bool = False
) -> ControllerReturn:
    """Runs the APVI crawl definition"""
    apvi_return = ControllerReturn()

    if crawler.latest:
        apvi_forecast_return = run_apvi_crawl()
        return apvi_forecast_return

    # run the entire date range
    elif crawler.limit:
        for date in date_series(get_today_nem().date(), length=crawler.limit, reverse=True):
            apvi_forecast_return = run_apvi_crawl(date)
            apvi_return.processed_records += apvi_forecast_return.processed_records
            apvi_return.total_records += apvi_forecast_return.total_records
            apvi_return.inserted_records += apvi_forecast_return.inserted_records
            apvi_return.errors += apvi_forecast_return.errors

            if not apvi_return.server_latest or apvi_return.server_latest < apvi_forecast_return.server_latest:
                apvi_return.server_latest = apvi_forecast_return.server_latest

    else:
        for date in date_series(get_today_nem().date(), APVI_MIN_DATE, reverse=True):
            apvi_forecast_return = run_apvi_crawl(date)
            apvi_return.processed_records += apvi_forecast_return.processed_records
            apvi_return.total_records += apvi_forecast_return.total_records
            apvi_return.inserted_records += apvi_forecast_return.inserted_records
            apvi_return.errors += apvi_forecast_return.errors

            if not apvi_return.server_latest or apvi_return.server_latest < apvi_forecast_return.server_latest:
                apvi_return.server_latest = apvi_forecast_return.server_latest

    return apvi_return


def run_apvi_crawl(day: datetime | None = None) -> ControllerReturn:
    apvi_forecast_set: APVIForecastSet | None = None

    if day:
        logger.info(f"Getting APVI data for day {day}")
        apvi_forecast_set = get_apvi_rooftop_data(day)
    else:
        logger.info("Getting APVI data from today")
        apvi_forecast_set = get_apvi_rooftop_today()

    if not apvi_forecast_set:
        raise Exception("Could not get APVI forecast set")

    cr = store_apvi_forecastset(apvi_forecast_set)

    update_apvi_facility_capacities(apvi_forecast_set)

    cr.server_latest = apvi_forecast_set.server_latest

    return cr


APVIRooftopTodayCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.frequent,
    name="apvi.today.data",
    url="none",
    latest=True,
    processor=crawl_apvi_forecasts,
)

APVIRooftopLatestCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.four_times_a_day,
    name="apvi.latest.data",
    limit=3,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


APVIRooftopMonthCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="apvi.month.data",
    limit=30,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


APVIRooftopAllCrawler = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.daily,
    name="apvi.all.data",
    limit=None,
    url="none",
    latest=False,
    processor=crawl_apvi_forecasts,
)


if __name__ == "__main__":
    r = get_apvi_rooftop_data()

    if not r:
        print("no result")
    else:
        cr = store_apvi_forecastset(r)
        print(cr)
