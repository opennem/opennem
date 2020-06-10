from scrapy import Spider

from opennem.pipelines.nem import DatabaseStore, ExtractCSV


class WemFacilities(Spider):
    name = "au.wem.facilities"
    start_urls = [
        "http://data.wa.aemo.com.au/datafiles/facilities/facilities.csv"
    ]
    allowed_domains = ["wa.nemweb.com.au"]
    pipelines = set([ExtractCSV, DatabaseStore,])

    def parse(self, response):
        if response:
            yield {
                "link": response.url,
                "table_name": "facilities",
                "content": response.text,
                "type": "file",
            }
