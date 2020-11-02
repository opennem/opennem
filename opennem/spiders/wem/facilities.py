from opennem.pipelines.wem.facilities import (
    WemStoreFacility,
    WemStoreLiveFacilities,
)
from opennem.spiders.wem import WemCurrentSpider


class WemLiveFacilities(WemCurrentSpider):
    name = "au.wem.live.facilities"

    pipelines_extra = set([WemStoreLiveFacilities])

    start_url = (
        "https://aemo.com.au/aemo/data/wa/infographic/facility-meta.csv"
    )


class WemFacilities(WemCurrentSpider):
    name = "au.wem.facilities"
    start_url = (
        "http://data.wa.aemo.com.au/datafiles/facilities/facilities.csv"
    )

    pipelines_extra = set([WemStoreFacility])
