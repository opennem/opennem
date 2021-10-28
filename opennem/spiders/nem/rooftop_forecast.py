import re

from opennem.pipelines.bulk_insert import BulkInsertPipeline
from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.nem.opennem import NemwebUnitScadaOpenNEMStorePipeline
from opennem.spiders.nemweb import NemwebSpider


class NemwebLatestRooftopForecast(NemwebSpider):
    process_latest = True
    name = "au.nem.latest.rooftop_forecast"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/"
    limit = 2

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )


class NemwebDayRooftopForecast(NemwebSpider):
    name = "au.nem.day.rooftop_forecast"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/"
    limit = 2 * 24

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )


class NemwebCurrentRooftopForecast(NemwebSpider):
    name = "au.nem.current.rooftop_forecast"
    start_url = "http://www.nemweb.com.au/Reports/CURRENT/ROOFTOP_PV/FORECAST/"

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )


class NemwebArchiveRooftopForecast(NemwebSpider):
    name = "au.nem.archive.rooftop_forecast"
    start_url = "http://www.nemweb.com.au/Reports/ARCHIVE/ROOFTOP_PV/FORECAST/"

    filename_filter = re.compile(r".*_MEASUREMENT_.*")

    pipelines_extra = set(
        [
            NemwebUnitScadaOpenNEMStorePipeline,
            BulkInsertPipeline,
            RecordsToCSVPipeline,
        ]
    )
