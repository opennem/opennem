from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebCurrentDispatch(NemwebSpider):
    name = "au.nem.current.dispatch"
    start_url = "http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/"

    # only get most recent
    limit = 1

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])


class NemwebArchiveDispatch(NemwebSpider):
    name = "au.nem.archive.dispatch"
    start_url = "http://nemweb.com.au/Reports/Current/Next_Day_Dispatch/"
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 4,
        "CONCURRENT_ITEMS": 1,
    }
