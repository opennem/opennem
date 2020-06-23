from opennem.spiders.wem_base import WemHistoricSpider


class WemHistoricBalancingSummary(WemHistoricSpider):
    name = "au.wem.historic.balancing_summary"
    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/"

    limit = 0
