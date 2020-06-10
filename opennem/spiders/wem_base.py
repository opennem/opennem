
import logging

import scrapy

from opennem.pipelines.files import LinkExtract
from opennem.pipelines.nem import DatabaseStore, ExtractCSV
from opennem.spiders.dirlisting import DirlistingSpider


class WemSpider(DirlistingSpider):
    allowed_domains = ["wa.nemweb.com.au"]
    pipelines = set([
        LinkExtract,
        ExtractCSV,
        DatabaseStore,
    ])
