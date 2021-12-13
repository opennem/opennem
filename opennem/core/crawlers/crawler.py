"""Get crawl metadata info from storage

"""

from datetime import datetime
from typing import List, Optional

from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig


class CrawlMetadata(BaseConfig):
    name: str
    last_crawled: Optional[datetime]
    last_processed: Optional[datetime]


def crawlers_get_crawl_metadata() -> List[CrawlMetadata]:
    """Get a return of metadata schemas for all crawlers from the database"""
    engine = get_database_engine()

    __query = """
        select
            cm.spider_name,
            cm.data->>'last_crawled' as last_crawled,
            cm.data->>'last_processed' as last_processed
        from crawl_meta cm
        order by last_crawled desc;
    """

    with engine.connect() as c:
        pass

    pass


if __name__ == "__main__":
    pass
