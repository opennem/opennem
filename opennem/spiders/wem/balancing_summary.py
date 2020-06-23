import csv

import scrapy

from opennem.pipelines.wem import WemStoreBalancingSummary
from opennem.spiders.wem_base import WemHistoricSpider


class WemCurrentBalancingSummary(scrapy.Spider):
    name = "au.wem.current.balancing_summary"
    start_urls = [
        "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/balancing-summary-2020.csv"
    ]
    pipelines_extra = set([WemStoreBalancingSummary])

    # def open_spider(self, spider):
    #     pass

    def parse(self, response):
        csvreader = csv.DictReader(response.text.split("\n"))
        for row in csvreader:
            yield row


class WemHistoricBalancingSummary(WemHistoricSpider):
    name = "au.wem.historic.balancing_summary"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/"

    limit = 0
