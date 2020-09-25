from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebCurrentDispatchScada(NemwebSpider):
    name = "au.nem.current.dispatch_scada"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])


class NemwebArchiveDispatchScada(NemwebSpider):
    name = "au.nem.archive.dispatch_scada"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
    limit = 0

    pipelines_extra = set([NemwebUnitScadaOpenNEMStorePipeline,])

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_ITEMS": 1,
    }
