from typing import Generator

import scrapy

from opennem.spiders.bom.bom_base import BomJSONObservationSpider

from .utils import BOM_REQUEST_HEADERS, get_stations, get_stations_priority


class BomCapitalsSpider(BomJSONObservationSpider):
    name = "bom.capitals"

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        priority_stations = get_stations_priority()

        _headers = BOM_REQUEST_HEADERS.copy()

        for station in priority_stations:
            yield scrapy.Request(station.feed_url, meta={"code": station.code}, headers=_headers)


class BomAllSpider(BomJSONObservationSpider):
    # name = "bom.all"

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        stations = get_stations()

        _headers = BOM_REQUEST_HEADERS.copy()

        for station in stations:
            yield scrapy.Request(station.feed_url, meta={"code": station.code}, headers=_headers)
