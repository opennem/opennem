import scrapy
from scrapy import Spider
from scrapy.http import Request, Response


class AEMOMonitorRelSpider(Spider):

    name = "au.aemo.monitor.rel"

    start_urls = [
        "https://aemo.com.au/en/energy-systems/electricity/national-electricity-market-nem/participate-in-the-market/registration"
    ]

    def parse(self, response: Response) -> None:
        selector = response.css("div.field-publisheddate")

        self.log(selector)
