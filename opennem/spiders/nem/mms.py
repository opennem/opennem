import scrapy

from opennem.pipelines.nem.stations import (
    NemStoreMMSStations,
    NemStoreMMSStationStatus,
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
