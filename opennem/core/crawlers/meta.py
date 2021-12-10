"""
OpenNEM Crawler Meta

Gets metadata about crawls from the database
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import CrawlMeta
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.spider.meta")


class CrawlStatTypes(Enum):
    last_crawled = "last_crawled"
    latest_processed = "latest_processed"
    data = "data"


class CrawlMetadata(BaseConfig):
    name: str
    last_crawled: Optional[datetime]
    last_processed: Optional[datetime]


def crawler_get_all_meta(crawler_name: str) -> Optional[Dict[str, Any]]:
    session = SessionLocal()

    spider_meta = session.query(CrawlMeta).filter_by(spider_name=crawler_name).one_or_none()

    if not spider_meta:
        return None

    if not spider_meta.data:
        return None

    return spider_meta.data


def crawler_get_meta(crawler_name: str, key: CrawlStatTypes) -> Optional[Union[str, datetime]]:
    session = SessionLocal()

    spider_meta = session.query(CrawlMeta).filter_by(spider_name=crawler_name).one_or_none()

    if not spider_meta:
        return None

    if not spider_meta.data:
        return None

    if key.value not in spider_meta.data:
        return None

    _val = spider_meta.data[key.value]

    if key in [CrawlStatTypes.latest_processed, CrawlStatTypes.last_crawled]:
        _val_processed = datetime.fromisoformat(_val)
        return _val_processed

    return _val


def crawler_set_meta(crawler_name: str, key: CrawlStatTypes, value: Any) -> None:
    session = SessionLocal()

    if key == CrawlStatTypes.latest_processed:
        current_value = crawler_get_meta(crawler_name, key)

        try:
            if current_value and current_value >= value:
                return None
        except TypeError:
            logger.error(
                "Error comparing {} ({}) and {} ({})".format(
                    current_value, type(current_value), value, type(value)
                )
            )

    spider_meta = session.query(CrawlMeta).filter_by(spider_name=crawler_name).one_or_none()

    if not spider_meta:
        spider_meta = CrawlMeta(spider_name=crawler_name, data={})

    spider_meta.data[key.value] = value

    logger.info("Spider {} meta: Set {} to {}".format(crawler_name, key.value, value))

    session.add(spider_meta)
    session.commit()


if __name__ == "__main__":
    crawler_set_meta("au.nem.latest.dispatch_scada", CrawlStatTypes.last_crawled, datetime.now())
