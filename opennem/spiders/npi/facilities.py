# @TODO crawl
#
import scrapy

from opennem.pipelines.npi.facilities import NPIStoreFacility

NPI_GEOJSON_URL = "https://data.gov.au/geoserver/npi/wfs?request=GetFeature&typeName=ckan_043f58e0_a188_4458_b61c_04e5b540aea4&outputFormat=json"


class NPIFacilitySpider(scrapy.Spider):
    # name = "au.npi.facilities"

    start_urls = [NPI_GEOJSON_URL]

    pipelines = set([NPIStoreFacility])

    def parse(self, response):
        yield {"records": response.json()}
