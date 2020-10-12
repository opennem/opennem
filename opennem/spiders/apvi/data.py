from datetime import datetime, timedelta

import scrapy

from opennem.pipelines.apvi.data import APVIStoreData
from opennem.utils.dates import date_series, get_date_component

APVI_DATA_URI = "https://pv-map.apvi.org.au/data"


class APVIDataSpiderBase(scrapy.Spider):

    name = "au.apvi.latest.data"

    pipelines = set([APVIStoreData])

    def start_requests(self):
        yield scrapy.FormRequest(
            APVI_DATA_URI, formdata={"day": get_date_component("%Y-%m-%d")}
        )

    def parse(self, response):
        yield {"records": response.json()}


class APVIDataCurrentSpider(APVIDataSpiderBase):
    name = "au.apvi.current.data"

    def start_requests(self):
        yesterday = datetime.now().date() - timedelta(days=1)

        for date in date_series(yesterday):
            yield scrapy.FormRequest(
                APVI_DATA_URI, formdata={"day": date.strftime("%Y-%m-%d")}
            )
