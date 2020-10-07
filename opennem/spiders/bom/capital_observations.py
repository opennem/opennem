import scrapy

from opennem.spiders.bom.bom_base import BomJSONObservationSpider

from .utils import get_stations, get_stations_priority


class BomCapitalsSpider(BomJSONObservationSpider):
    name = "bom.capitals"

    def start_requests(self):
        priority_stations = get_stations_priority()

        for station in priority_stations:
            yield scrapy.Request(station.feed_url, meta={"code": station.code})


class BomAllSpider(BomJSONObservationSpider):
    name = "bom.all"

    def start_requests(self):
        station = get_stations()

        for station in station:
            yield scrapy.Request(station.feed_url, meta={"code": station.code})
