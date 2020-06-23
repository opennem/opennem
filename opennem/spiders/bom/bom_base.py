import json
import logging

import scrapy

from opennem.pipelines.bom import StoreBomObservation


class BomJSONObservationSpider(scrapy.Spider):
    allowed_domains = ["bom.gov.au"]
    start_urls = ["http://reg.bom.gov.au/fwo/IDN60901/IDN60901.94767.json"]
    pipelines = set([StoreBomObservation])

    def parse(self, response):
        json_response = json.loads(response.text)

        if not type(json_response) is dict:
            raise Exception("invalid response from bom")

        if not "observations" in json_response:
            raise Exception("invalid response from bom")

        if not "data" in json_response["observations"]:
            raise Exception("invalid response from bom")

        for i in json_response["observations"]["data"]:
            yield i
