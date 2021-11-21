"""APVI Rooftop Data Crawler

"""

import logging
from datetime import datetime

from opennem.clients.apvi import APVIForecastSet, get_apvi_rooftop_data
from opennem.controllers.apvi import store_apvi_forecastset, update_apvi_facility_capacities
from opennem.controllers.schema import ControllerReturn
from opennem.crawlers.schema import CrawlerDefinition
from opennem.utils.dates import date_series

logger = logging.getLogger("opennem.crawlers.apvi")


def crawl_apvi_forecasts(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    apvi_forecast_set = get_apvi_rooftop_data()

    if not apvi_forecast_set:
        raise Exception("Could not get APVI forecast set")

    cr = store_apvi_forecastset(apvi_forecast_set)

    update_apvi_facility_capacities(apvi_forecast_set)

    cr.last_modified = datetime.now()

    return cr


if __name__ == "__main__":
    r = get_apvi_rooftop_dat()
    cr = store_apvi_forecastset(r)
    print(cr)
