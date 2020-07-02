import logging
import re
from datetime import datetime

import scrapy
from scrapy import Spider

from opennem.datetimes import parse_date

PADDING_WIDTH = 3

__is_number = re.compile(r"^\d+$")


def is_number(value):
    if re.match(__is_number, value):
        return True
    return False


def parse_dirlisting(raw_string):
    """
        given a raw text directory listing like "     Saturday 11th June 2020      6789"
        will parse and return both the date and listing type

        @param raw_string - the raw directory listing string
        @return dict of the date in iso format and the type (file or directory)
    """
    components = raw_string.split(" " * PADDING_WIDTH)
    components = [i.strip() for i in components]
    components = list(filter(lambda x: x != "", components))

    _ltype = "dir"

    if not components or len(components) < 2:
        logging.debug(components)
        raise Exception(
            "Invalid line string: {}. Components are: {}".format(
                raw_string, components
            )
        )

    if is_number(components[1]):
        _ltype = "file"

    dt = parse_date(components[0])

    if type(dt) is not datetime:
        raise Exception(
            "{} is not a valid datetime. Original value was {}".format(
                dt, components[0]
            )
        )

    return {
        "date": dt.isoformat(),
        "type": _ltype,
    }


class DirlistingSpider(Spider):
    """
        spider that parses html directory listings produced by web servers


    """

    limit = 0

    def start_requests(self):
        if self.custom_settings is None:
            self.custom_settings = {}

        starts = None

        if (
            hasattr(self, "start_url")
            and self.start_url
            and type(self.start_url) is str
        ):
            starts = [self.start_url]

        if (
            hasattr(self, "start_urls")
            and self.start_urls
            and type(self.start_urls) is list
        ):
            starts = [self.start_urls]

        for url in starts:
            yield scrapy.Request(url)

    def parse(self, response):
        links = list(
            reversed(
                [
                    i.get()
                    for i in response.xpath(
                        "//body/pre/br/following-sibling::a/@href"
                    )
                ]
            )
        )

        metadata = list(
            reversed(
                [
                    parse_dirlisting(i.get())
                    for i in response.xpath(
                        "//body/pre/br/following-sibling::text()"
                    )
                ]
            )
        )

        parsed = 0

        for i, entry in enumerate(metadata):
            if entry["type"] == "file":
                link = response.urljoin(links[i])

                self.log("Getting {}".format(link), logging.INFO)

                if self.limit and self.limit > 0 and (parsed >= self.limit):
                    self.log(f"Reached limit of {self.limit}", logging.INFO)
                    return None

                parsed += 1

                yield {"link": link, **entry}
