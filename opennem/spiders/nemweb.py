"""
OpenNEM Base Nemweb Spider


This is the base nemweb spider that all the other spiders inherit from. It
simply sets up the allowed domain and the defauly pipelines applied.


"""

from opennem.pipelines.files import LinkExtract
from opennem.pipelines.nem import ExtractCSV
from opennem.spiders.dirlisting import DirlistingSpider


class NemwebSpider(DirlistingSpider):
    """Base Nemweb spider - sets the allowed domains and the default
    pipelines to apply using the custom pipelines extension for OpenNEM"""

    allowed_domains = ["nemweb.com.au"]
    pipelines = set([LinkExtract, ExtractCSV])
