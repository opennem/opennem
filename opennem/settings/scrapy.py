"""
Scrapy settings for nemweb project

For simplicity, this file contains only settings considered important or
commonly used. You can find more settings consulting the documentation:

https://docs.scrapy.org/en/latest/topics/settings.html
"""

BOT_NAME = "opennem"
SPIDER_MODULES = ["opennem.spiders"]
NEWSPIDER_MODULE = "opennem.spiders"


USER_AGENT = "opennem/0.5.0 (+https://opennem.org.au)"
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 16
COOKIES_ENABLED = True
TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en",
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60


# Pipline docs:
# 1xx series - download handlers
# 2xx series - unpackers
# 3xx series -
# 4xx series - database processes
ITEM_PIPELINES = {
    # Generic Pipelines
    "opennem.pipelines.files.LinkExtract": 101,
    "opennem.pipelines.nem.UnzipSingleFilePipeline": 302,
    "opennem.pipelines.nem.ReadStringHandle": 310,
    "opennem.pipelines.nem.ExtractCSV": 320,
    "opennem.pipelines.nem.TableRecordSplitter": 330,
    # AEMO XLS Parsers
    "opennem.pipelines.aemo.registration_exemption.RegistrationExemptionGrouperPipeline": 350,
    "opennem.pipelines.aemo.general_information.GeneralInformationGrouperPipeline": 351,
    "opennem.pipelines.aemo.registration_exemption.RegistrationExemptionStorePipeline": 355,
    "opennem.pipelines.aemo.general_information.GeneralInformationStoragePipeline": 356,
    # Opennem storers
    "opennem.pipelines.nem.DatabaseStore": 400,
    "opennem.pipelines.wem.facilities.WemStoreFacility": 410,
    "opennem.pipelines.wem.facility_scada.WemStoreFacilityScada": 411,
    "opennem.pipelines.wem.balancing_summary.WemStoreBalancingSummary": 412,
    "opennem.pipelines.wem.balancing_summary.WemStoreBalancingSummaryArchive": 413,
    "opennem.pipelines.wem.pulse.WemStorePulse": 414,
    "opennem.pipelines.wem.facility_scada.WemStoreLiveFacilityScada": 415,
    "opennem.pipelines.wem.facilities.WemStoreLiveFacilities": 416,
    "opennem.pipelines.wem.participant.WemStoreParticipant": 417,
    "opennem.pipelines.wem.participant.WemStoreLiveParticipant": 418,
    # BOM Storers
    "opennem.pipelines.bom.StoreBomObservation": 430,
    # MMS Parsers and Storers
    "opennem.pipelines.nem.mms_dudetailsummary.AEMOMMSDudetailSummaryGrouper": 504,
    "opennem.pipelines.nem.mms.NemStoreMMSStations": 551,
    "opennem.pipelines.nem.mms.NemStoreMMSStationStatus": 552,
    "opennem.pipelines.nem.mms.NemStoreMMSDudetail": 553,
    "opennem.pipelines.nem.mms.NemStoreMMSDudetailSummary": 554,
    "opennem.pipelines.nem.mms.NemStoreMMSParticipant": 555,
}

# @TODO if DEBUG
HTTPCACHE_ENABLED = True
HTTPCACHE_DIR = ".scrapy"
