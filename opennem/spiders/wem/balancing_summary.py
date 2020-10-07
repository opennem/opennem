from opennem.pipelines.wem.balancing_summary import WemStoreBalancingSummary
from opennem.spiders.wem import WemCurrentSpider, WemHistoricSpider


class WemCurrentBalancingSummary(WemCurrentSpider):
    name = "au.wem.current.balancing_summary"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/balancing-summary-{year}.csv"

    pipelines_extra = set([WemStoreBalancingSummary])


class WemHistoricBalancingSummary(WemHistoricSpider):
    name = "au.wem.historic.balancing_summary"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/"
    limit = 0

    pipelines_extra = set([WemStoreBalancingSummary])
