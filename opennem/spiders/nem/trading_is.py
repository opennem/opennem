# from opennem.pipelines.bulk_insert import BulkInsertPipeline
# from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebLatestTradingIS(NemwebSpider):
    name = "au.nem.latest.trading_is"
    start_url = "http://nemweb.com.au/Reports/Current/TradingIS_Reports/"
    limit = 2

    # only get most recent
    # limit = 1

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            # BulkInsertPipeline,
            # RecordsToCSVPipeline,
        ]
    )


class NemwebCurrentTradingIS(NemwebSpider):
    name = "au.nem.current.trading_is"
    start_url = "http://nemweb.com.au/Reports/Current/TradingIS_Reports/"
    limit = 0

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            # BulkInsertPipeline,
            # RecordsToCSVPipeline,
        ]
    )


class NemwebArchiveTradingIS(NemwebSpider):
    name = "au.nem.archive.trading_is"
    start_url = "http://nemweb.com.au/Reports/Archive/TradingIS_Reports/"
    limit = 0

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            # BulkInsertPipeline,
            # RecordsToCSVPipeline,
        ]
    )

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
    }
