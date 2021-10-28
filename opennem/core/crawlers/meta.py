"""
OpenNEM Crawler Meta

Gets metadata about crawls from the database
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from scrapy import Spider

from opennem.db import SessionLocal
from opennem.db.models.opennem import CrawlMeta
from opennem.spiders.aemo.monitoring import AEMOMonitorRelSpider

logger = logging.getLogger("opennem.spider.meta")


class CrawlStatTypes(Enum):
    last_crawled = "last_crawled"
    latest_processed = "latest_processed"
    data = "data"


def crawler_get_meta(spider: Spider, key: CrawlStatTypes) -> Optional[Union[str, datetime]]:
    session = SessionLocal()

    spider_meta = session.query(CrawlMeta).filter_by(spider_name=spider.name).one_or_none()

    if not spider_meta:
        return None

    if not spider_meta.data:
        return None

    if key.value not in spider_meta.data:
        return None

    return spider_meta.data[key.value]


def crawler_set_meta(spider: Spider, key: CrawlStatTypes, value: Any) -> None:
    session = SessionLocal()

    spider_meta = session.query(CrawlMeta).filter_by(spider_name=spider.name).one_or_none()

    if not spider_meta:
        spider_meta = CrawlMeta(spider_name=spider.name, data={})

    spider_meta.data[key.value] = value

    logger.info("Spider {} meta: Set {} to {}".format(spider.name, key.value, value))

    session.add(spider_meta)
    session.commit()


if __name__ == "__main__":
    crawler_set_meta(AEMOMonitorRelSpider, CrawlStatTypes.last_crawled, datetime.now())
