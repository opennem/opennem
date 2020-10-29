from opennem.pipelines.bulk_insert import BulkInsertPipeline
from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebLatestDispatchScada(NemwebSpider):
    name = "au.nem.latest.dispatch_scada"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
    limit = 2

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )


class NemwebCurrentDispatchScada(NemwebSpider):
    name = "au.nem.current.dispatch_scada"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
    limit = 0
    skip = 1

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )


class NemwebArchiveDispatchScada(NemwebSpider):
    name = "au.nem.archive.dispatch_scada"
    start_url = "http://www.nemweb.com.au/Reports/ARCHIVE/Dispatch_SCADA/"

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )

    # Archives tend to contain large zips of embedded zips so throttle
    # to limit memory use
    custom_settings = {
        "CONCURRENT_REQUESTS": 4,
        "CONCURRENT_ITEMS": 1,
    }

