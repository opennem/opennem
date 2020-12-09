from opennem.spiders.wem import WemHistoricSpider


class WemHistoricLoadSummary(WemHistoricSpider):
    name = "au.wem.archive.load_summary"
    start_urls = (
        "http://data.wa.aemo.com.au/public/public-data/datafiles/load-summary/"
    )
    limit = 0
