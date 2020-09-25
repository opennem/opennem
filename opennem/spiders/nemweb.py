from opennem.pipelines.files import LinkExtract
from opennem.pipelines.nem import DatabaseStore, ExtractCSV
from opennem.spiders.dirlisting import DirlistingSpider


class NemwebSpider(DirlistingSpider):
    allowed_domains = ["nemweb.com.au"]
    pipelines = set([LinkExtract, ExtractCSV, DatabaseStore,])
