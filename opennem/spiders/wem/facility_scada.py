from opennem.pipelines.bulk_insert import BulkInsertPipeline
from opennem.pipelines.csv import RecordsToCSVPipeline
from opennem.pipelines.wem.facility_scada import (
    WemStoreFacilityIntervals,
    WemStoreFacilityScada,
    WemStoreLiveFacilityScada,
)
from opennem.spiders.wem import WemCurrentSpider, WemHistoricSpider


class WemLiveFacilityScada(WemCurrentSpider):
    # name = "au.wem.live.facility_scada"
    pipelines_extra = set([WemStoreLiveFacilityScada])

    start_url = "https://aemo.com.au/aemo/data/wa/infographic/generation.csv"


class WemLiveFacilityIntervals(WemCurrentSpider):
    name = "au.wem.live.facility_intervals"
    pipelines_extra = set(
        [WemStoreFacilityIntervals, RecordsToCSVPipeline, BulkInsertPipeline]
    )

    start_url = "https://aemo.com.au/aemo/data/wa/infographic/facility-intervals-last96.csv"


class WemCurrentFacilityScada(WemCurrentSpider):
    name = "au.wem.current.facility_scada"
    pipelines_extra = set(
        [WemStoreFacilityScada, RecordsToCSVPipeline, BulkInsertPipeline]
    )

    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/facility-scada/facility-scada-{year}-{month}.csv"


class WemHistoricFacilityScada(WemHistoricSpider):
    name = "au.wem.archive.facility_scada"
    start_url = "http://data.wa.aemo.com.au/datafiles/facility-scada/"

    pipelines_extra = set(
        [WemStoreFacilityScada, RecordsToCSVPipeline, BulkInsertPipeline]
    )
