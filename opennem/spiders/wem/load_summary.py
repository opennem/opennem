
from opennem.spiders.wem_base import WemSpider


class WemCurrentLoadSummary(WemSpider):
    name = "au.wem.current.balancing_summary"
    start_urls = ["http://data.wa.aemo.com.au/public/public-data/datafiles/load-summary/"]
    limit = 0
