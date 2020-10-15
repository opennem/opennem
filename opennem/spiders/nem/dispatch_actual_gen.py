from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebDispatchActualGenLatest(NemwebSpider):
    name = "au.nem.latest.dispatch_actual_gen"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/"

    limit = 1

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline])


class NemwebDispatchActualGenCurrent(NemwebSpider):
    name = "au.nem.current.dispatch_actual_gen"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/Next_Day_Actual_Gen/"

    limit = 0
    skip = 1

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline])


class NemwebDispatchActualGenArchive(NemwebSpider):
    name = "au.nem.archive.dispatch_actual_gen"
    start_url = "http://www.nemweb.com.au/Reports/ARCHIVE/Next_Day_Actual_Gen/"
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline])

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
    }
