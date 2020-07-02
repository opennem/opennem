import csv

import scrapy

from opennem.pipelines.wem.facility_scada import WemStoreFacilityScada
from opennem.spiders.wem import WemCurrentSpider, WemHistoricSpider


class WemCurrentFacilityScada(WemCurrentSpider):
    name = "au.wem.current.facility_scada"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/facility-scada/facility-scada-{year}-{month}.csv"

    pipelines_extra = set([WemStoreFacilityScada])


class WemHistoricFacilityScada(WemHistoricSpider):
    name = "au.wem.historic.facility_scada"
    start_urls = ["http://data.wa.aemo.com.au/datafiles/facility-scada/"]

    pipelines_extra = set([WemStoreFacilityScada])
