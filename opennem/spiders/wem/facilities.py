import csv

from scrapy import Spider

from opennem.pipelines.wem import WemStoreFacility
from opennem.pipelines.wem.facilities import WemStoreLiveFacilities
from opennem.spiders.wem import WemCurrentSpider


class WemLiveFacilities(WemCurrentSpider):
    name = "au.wem.live.facilities"

    pipelines_extra = set([WemStoreLiveFacilities])

    start_url = (
        "https://aemo.com.au/aemo/data/wa/infographic/facility-meta.csv"
    )


class WemFacilities(Spider):
    name = "au.wem.facilities"
    start_urls = [
        "http://data.wa.aemo.com.au/datafiles/facilities/facilities.csv"
    ]
    # allowed_domains = ["wa.nemweb.com.au"]
    pipelines = set([WemStoreFacility,])

    def parse(self, response):
        csvreader = csv.DictReader(response.text.split("\n"))
        for row in csvreader:
            yield row
