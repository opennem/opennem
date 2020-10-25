from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebLatestPriceSpider(NemwebSpider):
    name = "au.nem.latest.price"
    start_url = (
        "http://www.nemweb.com.au/Reports/CURRENT/Dispatchprices_PRE_AP/"
    )
    limit = 2

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])


class NemwebCurrentPriceSpider(NemwebSpider):
    name = "au.nem.current.price"
    start_url = (
        "http://www.nemweb.com.au/Reports/CURRENT/Dispatchprices_PRE_AP/"
    )
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])


class NemwebArchivePriceSpider(NemwebSpider):
    name = "au.nem.archive.price"
    start_url = (
        "http://www.nemweb.com.au/Reports/ARCHIVE/Dispatchprices_PRE_AP/"
    )
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
    }
