from opennem.pipelines.wem.balancing_summary import (
    WemStoreBalancingSummary,
    WemStoreBalancingSummaryArchive,
)
from opennem.spiders.wem import WemCurrentSpider, WemHistoricSpider


class WemCurrentBalancingSummary(WemCurrentSpider):
    name = "au.wem.current.balancing_summary"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/balancing-summary-{year}.csv"

    pipelines_extra = set([WemStoreBalancingSummary])


class WemHistoricBalancingSummary(WemHistoricSpider):
    limit = 1
    name = "au.wem.historic.balancing_summary"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/"

    pipelines_extra = set([WemStoreBalancingSummaryArchive])
