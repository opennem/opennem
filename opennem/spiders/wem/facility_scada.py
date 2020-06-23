import csv

import scrapy

from opennem.pipelines.wem import WemStoreFacilityScada
from opennem.spiders.wem_base import WemHistoricSpider


class WemCurrentFacilityScada(scrapy.Spider):
    name = "au.wem.current.facility_scada"
    start_urls = [
        "http://data.wa.aemo.com.au/public/public-data/datafiles/facility-scada/facility-scada-2020-06.csv"
    ]
    pipelines_extra = set([WemStoreFacilityScada])

    def parse(self, response):
        csvreader = csv.DictReader(response.text.split("\n"))
        for row in csvreader:
            yield row


class WemHistoricFacilityScada(WemHistoricSpider):
    name = "au.wem.historic.facility_scada"
    start_urls = ["http://data.wa.aemo.com.au/datafiles/facility-scada/"]
    limit = 1
    pipelines_extra = set([WemStoreFacilityScada])
