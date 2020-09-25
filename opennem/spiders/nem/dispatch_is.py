from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebCurrentDispatchIS(NemwebSpider):
    name = "au.nem.current.dispatch_is"
    start_url = "http://nemweb.com.au/Reports/Current/DispatchIS_Reports/"
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])


class NemwebArchiveDispatchIS(NemwebSpider):
    name = "au.nem.archive.dispatch_is"
    start_url = "http://nemweb.com.au/Reports/Archive/DispatchIS_Reports/"
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
    }
