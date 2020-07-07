import csv

import scrapy

from opennem.pipelines.wem.facility_scada import (
    WemStoreFacilityScada,
    WemStoreLiveFacilityScada,
)
from opennem.spiders.wem import WemCurrentSpider, WemHistoricSpider


class WemLiveFacilityScada(WemCurrentSpider):
    name = "au.wem.live.facility_scada"
    pipelines_extra = set([WemStoreLiveFacilityScada])

    start_url = "https://aemo.com.au/aemo/data/wa/infographic/generation.csv"


class WemCurrentFacilityScada(WemCurrentSpider):
    name = "au.wem.current.facility_scada"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/facility-scada/facility-scada-{year}-{month}.csv"

    pipelines_extra = set([WemStoreFacilityScada])


class WemHistoricFacilityScada(WemHistoricSpider):
    name = "au.wem.historic.facility_scada"
    start_url = "http://data.wa.aemo.com.au/datafiles/facility-scada/"

    pipelines_extra = set([WemStoreFacilityScada])
