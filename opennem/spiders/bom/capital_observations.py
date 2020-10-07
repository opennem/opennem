import scrapy

from opennem.core.loader import load_data
from opennem.spiders.bom.bom_base import BomJSONObservationSpider

OBSERVATION_DATA = load_data("observatory_map.json", from_project=True)

CAPITAL_FEELDS = list(
    filter(lambda s: s["is_capital"] is True, OBSERVATION_DATA)
)


BOM_REMAINDER = list(
    filter(lambda s: s["is_capital"] is False, OBSERVATION_DATA)
)


class BomCapitalsSpider(BomJSONObservationSpider):
    name = "bom.capitals"

    def start_requests(self):
        for feed in CAPITAL_FEELDS:
            yield scrapy.Request(feed["feed"], meta=feed)


class BomAllSpider(BomJSONObservationSpider):
    name = "bom.all"

    def start_requests(self):
        for feed in BOM_REMAINDER:
            yield scrapy.Request(feed["feed"], meta=feed)


class BomSydneySpider(BomJSONObservationSpider):
    name = "bom.capitals.sydney"
    start_urls = ["http://reg.bom.gov.au/fwo/IDN60901/IDN60901.94767.json"]
    station_id = "066037"


class BomMelbourneSpider(BomJSONObservationSpider):
    name = "bom.capitals.melbourne"
    start_urls = ["http://reg.bom.gov.au/fwo/IDV60901/IDV60901.94866.json"]
    station_id = "086282"


class BomBrisbaneSpider(BomJSONObservationSpider):
    name = "bom.capitals.brisbane"
    start_urls = ["http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94576.json"]
    station_id = "040913"


class BomPerthSpider(BomJSONObservationSpider):
    name = "bom.capitals.perth"
    start_urls = ["http://reg.bom.gov.au/fwo/IDW60901/IDW60901.94610.json"]
    station_id = "009021"
