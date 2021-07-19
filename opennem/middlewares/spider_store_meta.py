"""
OpenNEM Scrapy Extension Spider Store Meta

Stores metadata about a spider crawl
"""

import logging
from datetime import datetime

from scrapy import signals
from scrapy.exceptions import NotConfigured

from opennem.core.crawlers.meta import CrawlStatTypes, crawler_set_meta

logger = logging.getLogger("opennem.extensions.spider_store_meta")


class ExtensionSpiderStoreMeta:
    def __init__(self):
        self.items_scraped = 0

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        # return the extension object
        return ext

    def spider_opened(self, spider):
        logger.info("opened spider %s", spider.name)

        print(spider.met)

    def spider_closed(self, spider):
        logger.info("closed spider %s", spider.name)

        crawler_set_meta(spider, CrawlStatTypes.last_crawled, datetime.now())
