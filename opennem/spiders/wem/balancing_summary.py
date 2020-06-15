
from opennem.spiders.wem_base import WemSpider


class WemCurrentBalancingSummary(WemSpider):
    name = "au.wem.current.balancing_summary"
    start_urls = ["http://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/"]
    limit = 0
