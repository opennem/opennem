"""
    Script to crawl BOM stations and output fields to json

    http://www.bom.gov.au/catalogue/data-feeds.shtml

    (c) OpenNEM 2020. https://opennem.org.au

    Data © Copyright Commonwealth of Australia 2020, Bureau of Meteorology (ABN 92 637 533 532)
"""

import logging
import os
import re
import sys

from scrapy import Field, Item, Spider
from scrapy.crawler import CrawlerProcess
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose, TakeFirst
from scrapy.settings import Settings

OUTPUT_FILENAME = "opennem/data/bom_stations.json"

logging.basicConfig(level=logging.INFO)


def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)


def parse_name(name=None):
    if not name:
        return None

    name = name.replace(os.linesep, "").replace("\r", "")
    return re.sub(r"\s+", " ", name).strip().title()


def clean_table_string(code: str = None):
    if not code:
        return None

    code: str = code.strip()

    if code == " " or code == "":
        return None

    if code in ["ID:", "Name:", "Lat:", "Lon:"]:
        return None

    return code


class BomStation(Item):
    code = Field()
    name = Field()
    name_full = Field()
    url = Field()
    json_feed = Field()
    lat = Field()
    lng = Field()


class BomStationItemLoader(ItemLoader):
    default_input_processor = MapCompose(str.strip)
    default_output_processor = Join()

    code_in = MapCompose(clean_table_string)
    name_full_in = MapCompose(clean_table_string)
    lat_in = MapCompose(clean_table_string, lambda x: float(x))
    lat_out = TakeFirst()
    lng_in = MapCompose(clean_table_string, lambda x: float(x))
    lng_out = TakeFirst()

    # name_in = MapCompose(parse_name)
    # state_in = MapCompose(str.strip, str.upper)


class StationCrawler(Spider):
    name = "stationcrawler"
    start_urls = [
        "http://www.bom.gov.au/nsw/observations/nswall.shtml",
        "http://www.bom.gov.au/nt/observations/ntall.shtml",
        "http://www.bom.gov.au/qld/observations/qldall.shtml",
        "http://www.bom.gov.au/sa/observations/saall.shtml",
        "http://www.bom.gov.au/tas/observations/tasall.shtml",
        "http://www.bom.gov.au/vic/observations/vicall.shtml",
        "http://www.bom.gov.au/wa/observations/waall.shtml",
    ]
    limit = 0

    def parse(self, response):
        for sel in response.css("table.tabledata > tbody > tr > th"):
            link = sel.css("a::attr('href')").get()
            name = sel.css("a::text").get()

            yield response.follow(
                link, self.parse_station_page, meta={"name": name}
            )

    def parse_station_page(self, response):
        loader = BomStationItemLoader(BomStation(), response=response)
        loader.add_value("name", response.meta["name"])
        loader.add_value("url", response.url)

        # if table:
        loader.add_xpath(
            "code",
            "//table[contains(@class, 'stationdetails')]//td[2]//text()",
        )
        loader.add_xpath(
            "name_full",
            "//table[contains(@class, 'stationdetails')]//td[3]//text()",
        )
        loader.add_xpath(
            "lat",
            "//table[contains(@class, 'stationdetails')]//td[4]//text()",
        )
        loader.add_xpath(
            "lng",
            "//table[contains(@class, 'stationdetails')]//td[5]//text()",
        )

        # find json link
        links = response.css("p.noPrint > a::attr('href')")
        for i in links:
            link: str = i.get()
            if link.endswith(".json"):
                loader.add_value("json_feed", response.urljoin(link))

        yield loader.load_item()


settings = Settings(
    {
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": False,
        "HTTPCACHE_ENABLED": True,
        "AUTOTHROTTLE_ENABLED": True,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        "FEED_FORMAT": "json",
    }
)


if __name__ == "__main__":
    settings["FEED_URI"] = OUTPUT_FILENAME
    process = CrawlerProcess(settings)

    process.crawl(StationCrawler)

    process.start()
