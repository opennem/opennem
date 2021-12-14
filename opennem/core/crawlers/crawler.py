"""Get crawl metadata info from storage

"""

import logging
from datetime import datetime
from typing import List, Optional

from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.crawlers.crawler")


class CrawlMetadata(BaseConfig):
    name: str
    last_crawled: Optional[datetime]
    last_processed: Optional[datetime]
    force_run: bool = False


def crawlers_get_crawl_metadata() -> List[CrawlMetadata]:
    """Get a return of metadata schemas for all crawlers from the database"""
    engine = get_database_engine()

    __query = """
        select
            cm.spider_name as name,
            cm.data->>'last_crawled' as last_crawled,
            cm.data->>'last_processed' as last_processed
        from crawl_meta cm
        order by last_crawled desc;
    """
    _crawler_metas = []

    with engine.connect() as c:
        _crawler_metas = list(c.execute(__query))

    if not _crawler_metas:
        return []

    _crawler_meta_models = [CrawlMetadata(**i) for i in _crawler_metas]

    return _crawler_meta_models


# debug entry point
if __name__ == "__main__":
    metas = crawlers_get_crawl_metadata()

    for m in metas:
        logger.info("{} {} {}".format(m.name, m.last_crawled, m.last_processed))
