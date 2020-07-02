import logging
from datetime import datetime

import scrapy

from opennem.pipelines.files import LinkExtract
from opennem.pipelines.nem import ExtractCSV
from opennem.pipelines.wem.balancing_summary import WemStoreBalancingSummary
from opennem.spiders.dirlisting import DirlistingSpider


def get_date_component(format_str):
    return datetime.now().strftime(format_str)


class WemCurrentSpider(scrapy.Spider):

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


class WemHistoricSpider(DirlistingSpider):
    allowed_domains = ["wa.nemweb.com.au"]
    pipelines = set([LinkExtract,])

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 4,
        "CONCURRENT_ITEMS": 8,
    }
