"""APVI Rooftop Data Crawler

"""

import logging
from datetime import datetime

import pytz

from opennem.clients.apvi import get_apvi_rooftop_data
from opennem.controllers.apvi import store_apvi_forecastset, update_apvi_facility_capacities
from opennem.controllers.schema import ControllerReturn
from opennem.crawlers.schema import CrawlerDefinition
from opennem.utils.dates import chop_datetime_microseconds, date_series, get_today_nem

logger = logging.getLogger("opennem.crawlers.apvi")


def crawl_apvi_forecasts(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    """Runs the APVI crawl definition"""
    if not crawler.limit or crawler.limit == 1:
        apvi_forecast_return = run_apvi_crawl(get_today_nem())
        return apvi_forecast_return

    apvi_return = ControllerReturn()

    for date in date_series(get_today_nem().date(), length=crawler.limit, reverse=True):
        apvi_forecast_return = run_apvi_crawl(date)
        apvi_return.processed_records += apvi_forecast_return.processed_records
        apvi_return.total_records += apvi_forecast_return.total_records
        apvi_return.inserted_records += apvi_forecast_return.inserted_records
        apvi_return.errors += apvi_forecast_return.errors

        if (
            not apvi_return.last_modified
            or apvi_return.last_modified < apvi_forecast_return.last_modified
        ):
            apvi_return.last_modified = apvi_forecast_return.last_modified

    return apvi_return


def run_apvi_crawl(day: datetime) -> ControllerReturn:

    apvi_forecast_set = get_apvi_rooftop_data(day)

    logger.debug("Getting APVI data for day {}".format(day))

    if not apvi_forecast_set:
        raise Exception("Could not get APVI forecast set")

    cr = store_apvi_forecastset(apvi_forecast_set)

    update_apvi_facility_capacities(apvi_forecast_set)

    cr.last_modified = chop_datetime_microseconds(
        datetime.now().astimezone(pytz.timezone("Australia/Brisbane"))
    )

    return cr


if __name__ == "__main__":
    r = get_apvi_rooftop_data()

    if not r:
        print("no result")
    else:
        cr = store_apvi_forecastset(r)
        print(cr)
