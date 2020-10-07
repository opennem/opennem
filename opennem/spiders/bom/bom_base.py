import json

import scrapy

from opennem.pipelines.bom import StoreBomObservation


class BomJSONObservationSpider(scrapy.Spider):
    allowed_domains = ["bom.gov.au"]

    start_urls = ["http://reg.bom.gov.au/fwo/IDN60901/IDN60901.94767.json"]

    pipelines = set([StoreBomObservation])

    station_id: str = None

    def parse(self, response):
        json_response = json.loads(response.text)

        if not type(json_response) is dict:
            raise Exception("invalid response from bom")

        if "observations" not in json_response:
            raise Exception("invalid response from bom")

        if "data" not in json_response["observations"]:
            raise Exception("invalid response from bom")

        station_id = None

        if "station_id" in response.meta:
            station_id = response.meta["station_id"]

        elif hasattr(self, "station_id") and self.station_id:
            station_id = self.station_id

        if not station_id:
            raise Exception("No station id for this scrape can't join")

        for i in json_response["observations"]["data"]:
            i["station_id"] = station_id

            yield i
