import io

import scrapy

from opennem.pipelines.nem import (
    ExtractCSV,
    ReadStringHandle,
    TableRecordSplitter,
    UnzipSingleFilePipeline,
)
from opennem.utils.dates import get_date_component


class NemXLSSpider(scrapy.Spider):

    start_url = ""

    url_params = {
        "day": get_date_component("%d"),
        "month": get_date_component("%m"),
        "year": get_date_component("%Y"),
    }

    def start_requests(self):
        request_url = self.start_url.format(**self.url_params)

        yield scrapy.Request(request_url)

    def parse(self, response):
        yield {"content": response.text}


class NemSingleMMSSpider(scrapy.Spider):

    pipelines = set(
        [
            UnzipSingleFilePipeline,
            ReadStringHandle,
            ExtractCSV,
            TableRecordSplitter,
        ]
    )

    def start_requests(self):
        if not hasattr(self, "url") or not self.url:
            raise Exception("{} requires url parameter".format(self.__class__))

        yield scrapy.Request(self.url)

    def parse(self, response):
        yield {"body_stream": io.BytesIO(response.body)}
