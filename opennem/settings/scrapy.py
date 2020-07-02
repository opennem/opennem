"""
Scrapy settings for nemweb project

For simplicity, this file contains only settings considered important or
commonly used. You can find more settings consulting the documentation:

https://docs.scrapy.org/en/latest/topics/settings.html
"""

BOT_NAME = "opennem"
SPIDER_MODULES = ["opennem.spiders"]
NEWSPIDER_MODULE = "opennem.spiders"


USER_AGENT = "opennem (+https://opennem.org.au)"
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 16
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
    # "opennem.pipelines.wem.ExtractCSV": 302,
    "opennem.pipelines.nem.DatabaseStore": 401,
    "opennem.pipelines.wem.WemStoreFacility": 410,
    "opennem.pipelines.wem.facility_scada.WemStoreFacilityScada": 411,
    "opennem.pipelines.wem.balancing_summary.WemStoreBalancingSummary": 412,
    "opennem.pipelines.wem.balancing_summary.WemStoreBalancingSummaryArchive": 413,
    "opennem.pipelines.bom.StoreBomObservation": 430,
}

# @TODO if DEBUG
HTTPCACHE_ENABLED = False
HTTPCACHE_DIR = ".scrapy"
