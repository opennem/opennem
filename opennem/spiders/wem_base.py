import logging

import scrapy

from opennem.pipelines.files import LinkExtract
from opennem.pipelines.nem import ExtractCSV
from opennem.spiders.dirlisting import DirlistingSpider


class WemHistoricSpider(DirlistingSpider):
    allowed_domains = ["wa.nemweb.com.au"]
    pipelines = set([LinkExtract,])
