# from opennem.pipelines.bulk_insert import BulkInsertPipeline
# from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebLatestTradingIS(NemwebSpider):
    # process_latest = True
    name = "au.nem.latest.trading_is"
    start_url = "http://nemweb.com.au/Reports/Current/TradingIS_Reports/"
    limit = 3

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
        ]
    )


class NemwebTodayTradingIS(NemwebSpider):
    name = "au.nem.day.trading_is"
    start_url = "http://nemweb.com.au/Reports/Current/TradingIS_Reports/"
    limit = 12 * 24

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
        ]
    )


class NemwebCurrentTradingIS(NemwebSpider):
    name = "au.nem.current.trading_is"
    start_url = "http://nemweb.com.au/Reports/Current/TradingIS_Reports/"
    limit = 0

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
        ]
    )


class NemwebArchiveTradingIS(NemwebSpider):
    name = "au.nem.archive.trading_is"
    start_url = "http://nemweb.com.au/Reports/Archive/TradingIS_Reports/"
    limit = 0

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
        ]
    )

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
    }
