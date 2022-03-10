"""
OpenNEM Crawler Meta

Gets metadata about crawls from the database
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from opennem.db import get_scoped_session
from opennem.db.models.opennem import CrawlMeta

logger = logging.getLogger("opennem.spider.meta")


class CrawlStatTypes(Enum):
    # version of crawler
    # scrapy based is v1
    # new version is v2+
    version = "version"

    # last crawl run time
    last_crawled = "last_crawled"

    # last time it was processed (success on insert)
    latest_processed = "latest_processed"

    # the latest data from the server that was processed
    # ie. on AEMO sites this is the latest dirlisting modified time
    # available
    server_latest = "server_latest"

    # generic data holder for all metadata
    data = "data"


def crawler_get_all_meta(crawler_name: str) -> Optional[Dict[str, Any]]:
    """Get crawler metadata by crawler name"""
    with get_scoped_session() as session:
        spider_meta = session.query(CrawlMeta).filter_by(spider_name=crawler_name).one_or_none()

        if not spider_meta:
            return None

        if not spider_meta.data:
            return None

        return spider_meta.data


def crawler_get_meta(crawler_name: str, key: CrawlStatTypes) -> Optional[Union[str, datetime]]:
    """Crawler get specific stat type from metadata for crawler name"""
    with get_scoped_session() as session:

        spider_meta = session.query(CrawlMeta).filter_by(spider_name=crawler_name).one_or_none()

        if not spider_meta:
            return None

        if not spider_meta.data:
            return None

        if key.value not in spider_meta.data:
            return None

        _val = spider_meta.data[key.value]

        if key in [
            CrawlStatTypes.latest_processed,
            CrawlStatTypes.last_crawled,
            CrawlStatTypes.server_latest,
        ]:
            _val_processed = datetime.fromisoformat(_val)
            return _val_processed

        return _val


def crawler_set_meta(crawler_name: str, key: CrawlStatTypes, value: Any) -> None:
    """Set a crawler metadata stat type by name"""
    with get_scoped_session() as session:
        if key == CrawlStatTypes.server_latest:
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

        logger.debug("Spider {} meta: Set {} to {}".format(crawler_name, key.value, value))

        session.add(spider_meta)
        session.commit()


if __name__ == "__main__":
    crawler_set_meta("au.nem.latest.dispatch_scada", CrawlStatTypes.last_crawled, datetime.now())
