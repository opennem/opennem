
import csv
import logging
import re

import scrapy
from requests.exceptions import HTTPError

from opennem.datetimes import parse_date
from opennem.pipelines.files import LinkExtract
from opennem.pipelines.nem import DatabaseStore, ExtractCSV
from opennem.spiders.dirlisting import DirlistingSpider
from opennem.utils.handlers import open


class NemwebSpider(DirlistingSpider):
    allowed_domains = ["nemweb.com.au"]
    pipelines = set([
        LinkExtract,
        ExtractCSV,
        DatabaseStore,
    ])
