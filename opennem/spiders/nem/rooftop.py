import re

from opennem.pipelines.bulk_insert import BulkInsertPipeline
from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebLatestRooftopActual(NemwebSpider):
    name = "au.nem.latest.rooftop"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/"
    limit = 3

    # Ignore sat
    filename_filter = re.compile(r".*_MEASUREMENT_.*")

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )


class NemwebCurrentRooftopActual(NemwebSpider):
    name = "au.nem.current.rooftop"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/ACTUAL/"

    filename_filter = re.compile(r".*_MEASUREMENT_.*")

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )


class NemwebArchiveRooftopActual(NemwebSpider):
    name = "au.nem.archive.rooftop"
    start_url = "http://www.nemweb.com.au/Reports/ARCHIVE/ROOFTOP_PV/ACTUAL/"

    filename_filter = re.compile(r".*_MEASUREMENT_.*")

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )
