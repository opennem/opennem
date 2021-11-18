"""
OpenNEM Scrapy Extension Spider Store Meta

Stores metadata about a spider crawl
"""

import logging
from datetime import datetime

from scrapy import signals

from opennem.core.crawlers.meta import CrawlStatTypes, crawler_set_meta

logger = logging.getLogger("opennem.extensions.spider_store_meta")


class ExtensionSpiderStoreMeta:
    def __init__(self):  # type: ignore
        self.items_scraped = 0

    @classmethod
    def from_crawler(cls, crawler):  # type: ignore
        ext = cls()

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)

        # return the extension object
        return ext

    def spider_opened(self, spider):  # type: ignore
        logger.info("opened spider %s", spider.name)

    def spider_closed(self, spider):  # type: ignore
        logger.info("closed spider %s", spider.name)

        crawler_set_meta(spider.name, CrawlStatTypes.last_crawled, datetime.now())

        if hasattr(spider, "data"):
            crawler_set_meta(spider.name, CrawlStatTypes.data, spider.data)

    def item_scraped(self, item, spider):  # type: ignore
        if isinstance(item, dict) and "_data" in item:
            crawler_set_meta(spider.name, CrawlStatTypes.data, [i.json() for i in item["_data"]])
