"""APVI Rooftop Data Crawler

"""

import logging
from datetime import datetime

import pytz

from opennem.clients.apvi import get_apvi_rooftop_data
from opennem.controllers.apvi import store_apvi_forecastset, update_apvi_facility_capacities
from opennem.controllers.schema import ControllerReturn
from opennem.crawlers.schema import CrawlerDefinition
from opennem.utils.dates import chop_datetime_microseconds

logger = logging.getLogger("opennem.crawlers.apvi")


def crawl_apvi_forecasts(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    apvi_forecast_set = get_apvi_rooftop_data()

    if not apvi_forecast_set:
        raise Exception("Could not get APVI forecast set")

    cr = store_apvi_forecastset(apvi_forecast_set)

    update_apvi_facility_capacities(apvi_forecast_set)

    cr.last_modified = chop_datetime_microseconds(
        datetime.now().astimezone(pytz.timezone("Australia/Sydney"))
    )

    return cr


if __name__ == "__main__":
    r = get_apvi_rooftop_data()

    if not r:
        print("no result")
    else:
        cr = store_apvi_forecastset(r)
        print(cr)
