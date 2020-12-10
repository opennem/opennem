import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Generator

import scrapy

from opennem.pipelines.apvi.data import APVIStoreData
from opennem.utils.dates import date_series, get_date_component

logger = logging.getLogger(__name__)

APVI_DATA_URI = "https://pv-map.apvi.org.au/data"

TODAY = datetime.now().date()

YESTERDAY = TODAY - timedelta(days=1)

MONTH_AGO = TODAY - timedelta(days=29)

APVI_DATE_QUERY_FORMAT = "%Y-%m-%d"

APVI_EARLIEST_DATE = "2013-05-07"


class APVIDataSpiderBase(scrapy.Spider):

    name = "au.apvi.latest.data"

    pipelines = set([APVIStoreData])

    def start_requests(self) -> Generator[scrapy.FormRequest, None, None]:
        day = get_date_component(APVI_DATE_QUERY_FORMAT)

        logger.debug("Getting APVI data for day {}".format(day))

        yield scrapy.FormRequest(
            APVI_DATA_URI,
            formdata={"day": day},
            meta={
                "is_latest": True,
                "record_date": day,
            },
        )

    def parse(self, response: Any) -> Generator[Dict, None, None]:
        yield {"records": response.json(), "meta": response.meta}


class APVIDataCurrentSpider(APVIDataSpiderBase):
    name = "au.apvi.current.data"

    def start_requests(self) -> Generator[scrapy.FormRequest, None, None]:
        for date in date_series(TODAY, length=31, reverse=True):
            day = date.strftime(APVI_DATE_QUERY_FORMAT)

            logger.debug("Getting APVI data for day {}".format(day))

            yield scrapy.FormRequest(
                APVI_DATA_URI,
                formdata={"day": day},
                meta={"is_latest": True if date == TODAY else False},
            )


class APVIDataArchiveSpider(APVIDataSpiderBase):
    name = "au.apvi.archive.data"

    def start_requests(self) -> Generator[scrapy.FormRequest, None, None]:
        end_date = datetime.strptime(
            APVI_EARLIEST_DATE, APVI_DATE_QUERY_FORMAT
        ).date()

        for date in date_series(start=MONTH_AGO, end=end_date, reverse=True):
            day = date.strftime(APVI_DATE_QUERY_FORMAT)

            logger.debug("Getting APVI data for day {}".format(day))

            yield scrapy.FormRequest(
                APVI_DATA_URI,
                formdata={"day": day},
            )

    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 1,
    }
