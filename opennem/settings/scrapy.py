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
    "opennem.pipelines.files.LinkExtract": 101,
    "opennem.pipelines.nem.ExtractCSV": 301,
    "opennem.pipelines.nem.DatabaseStore": 400,
    "opennem.pipelines.nem.facilities.NemStoreMMS": 401,
    "opennem.pipelines.nem.facilities.NemStoreGI": 402,
    "opennem.pipelines.nem.facilities.NemStoreREL": 403,
    "opennem.pipelines.wem.facilities.WemStoreFacility": 410,
    "opennem.pipelines.wem.facility_scada.WemStoreFacilityScada": 411,
    "opennem.pipelines.wem.balancing_summary.WemStoreBalancingSummary": 412,
    "opennem.pipelines.wem.balancing_summary.WemStoreBalancingSummaryArchive": 413,
    "opennem.pipelines.wem.pulse.WemStorePulse": 414,
    "opennem.pipelines.wem.facility_scada.WemStoreLiveFacilityScada": 415,
    "opennem.pipelines.wem.facilities.WemStoreLiveFacilities": 416,
    "opennem.pipelines.wem.participant.WemStoreParticipant": 417,
    "opennem.pipelines.wem.participant.WemStoreLiveParticipant": 418,
    "opennem.pipelines.bom.StoreBomObservation": 430,
}

# @TODO if DEBUG
HTTPCACHE_ENABLED = False
HTTPCACHE_DIR = ".scrapy"
