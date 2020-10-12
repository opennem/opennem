from datetime import datetime, timedelta

import scrapy

from opennem.pipelines.apvi.data import APVIStoreData
from opennem.utils.dates import date_series, get_date_component

APVI_DATA_URI = "https://pv-map.apvi.org.au/data"

TODAY = datetime.now().date()

YESTERDAY = TODAY - timedelta(days=1)

MONTH_AGO = TODAY - timedelta(days=29)

APVI_DATE_QUERY_FORMAT = "%Y-%m-%d"


class APVIDataSpiderBase(scrapy.Spider):

    name = "au.apvi.latest.data"

    pipelines = set([APVIStoreData])

    def start_requests(self):
        yield scrapy.FormRequest(
            APVI_DATA_URI,
            formdata={"day": get_date_component(APVI_DATE_QUERY_FORMAT)},
        )

    def parse(self, response):
        yield {"records": response.json()}


class APVIDataCurrentSpider(APVIDataSpiderBase):
    name = "au.apvi.current.data"

    def start_requests(self):
        for date in date_series(YESTERDAY):
            yield scrapy.FormRequest(
                APVI_DATA_URI,
                formdata={"day": date.strftime(APVI_DATE_QUERY_FORMAT)},
            )


class APVIDataHistoricSpider(APVIDataSpiderBase):
    name = "au.apvi.historic.data"

    def start_requests(self):
        for date in date_series(MONTH_AGO, length=90):
            yield scrapy.FormRequest(
                APVI_DATA_URI,
                formdata={"day": date.strftime(APVI_DATE_QUERY_FORMAT)},
            )
