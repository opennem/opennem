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

        code = None

        header = json_response["observations"]["header"][0]

        if "code" in response.meta:
            code = response.meta["code"]

        elif hasattr(self, "station_id") and self.station_id:
            code = self.station_id

        if not code:
            raise Exception("No station id for this scrape can't join")

        records = []

        for i in json_response["observations"]["data"]:
            i["code"] = code
            records.append(i)

        yield {"records": records, "header": header}
