
import logging
import re

import scrapy
from scrapy import Spider

from opennem.datetimes import parse_date

PADDING_WIDTH = 7

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

    if is_number(components[1]):
        _ltype = "file"

    return {
        "date": parse_date(components[0]).isoformat(),
        "type": _ltype,
    }

class DirlistingSpider(Spider):
    """
        spider that parses html directory listings produced by web servers


    """
    limit = 0

    def parse(self, response):
        links = [i.get() for i in response.xpath("//body/pre/br/following-sibling::a/@href")]
        metadata = [parse_dirlisting(i.get()) for i in response.xpath("//body/pre/br/following-sibling::text()")]

        parsed = 0

        for i, entry in enumerate(metadata):
            if entry["type"] == "file":
                link = response.urljoin(links[i])

                self.log("Getting {}".format(link), logging.INFO)

                if self.limit and self.limit > 0 and (parsed >= self.limit):
                    self.log(f"Reached limit of {self.limit}", logging.INFO)
                    return None

                parsed += 1

                yield from self.parse_entry({
                    "link": link,
                    **entry
                })

    def parse_entry(self, entry):
        yield entry
