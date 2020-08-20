import scrapy

from opennem.pipelines.nem import (
    ExtractCSV,
    ReadStringHandle,
    TableRecordSplitter,
    UnzipSingleFilePipeline,
)
from opennem.pipelines.nem.mms import (
    NemStoreMMSDudetail,
    NemStoreMMSDudetailSummary,
    NemStoreMMSParticipant,
    NemStoreMMSStatdualloc,
    NemStoreMMSStations,
    NemStoreMMSStationStatus,
)
from opennem.pipelines.nem.mms_dudetailsummary import (
    AEMOMMSDudetailSummaryGrouper,
)
from opennem.spiders.dirlisting import DirlistingSpider
from opennem.spiders.nem import NemSingleMMSSpider


class NemArchiveMMSSpider(DirlistingSpider):
    name = "au.nem.archive.mms"

    start_urls = [
        "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/"
    ]


class NemMMSStationSpider(NemSingleMMSSpider):
    name = "au.nem.mms.stations"

    pipelines_extra = set([NemStoreMMSStations])
    url = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_STATION_202006010000.zip"


class NemMMSStationStatusSpider(NemSingleMMSSpider):
    name = "au.nem.mms.stations_status"

    pipelines_extra = set([NemStoreMMSStationStatus])
    url = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_STATIONOPERATINGSTATUS_202006010000.zip"


class NemMMSParticipantSpider(NemSingleMMSSpider):
    name = "au.nem.mms.participant"

    pipelines_extra = set([NemStoreMMSParticipant])
    url = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_PARTICIPANT_202006010000.zip"


class NemMMSDudeTailSpider(NemSingleMMSSpider):
    name = "au.nem.mms.dudetail"

    pipelines_extra = set([NemStoreMMSDudetail,])
    url = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_DUDETAIL_202006010000.zip"


class NemMMSDudeTailSummarySpider(NemSingleMMSSpider):
    name = "au.nem.mms.dudetail_summary"

    # Override the base pipelines since we're using a grouper
    # @TODO make this generic
    pipelines = set(
        [
            UnzipSingleFilePipeline,
            ReadStringHandle,
            ExtractCSV,
            AEMOMMSDudetailSummaryGrouper,
        ]
    )

    pipelines_extra = set([NemStoreMMSDudetailSummary,])
    url = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_DUDETAILSUMMARY_202006010000.zip"


class NemMMSStaduAlloc(NemSingleMMSSpider):
    name = "au.nem.mms.statdualloc"

    pipelines_extra = set([NemStoreMMSStatdualloc,])
    url = "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/PUBLIC_DVD_STADUALLOC_202006010000.zip"
