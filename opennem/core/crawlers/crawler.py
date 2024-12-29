"""Get crawl metadata info from storage"""

import logging
from datetime import datetime

from sqlalchemy import text as sql

from opennem.db import db_connect_sync
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.crawlers.crawler")


class CrawlMetadata(BaseConfig):
    name: str
    version: float | None = None
    last_crawled: datetime | None = None
    last_processed: datetime | None = None
    server_latest: datetime | None = None
    force_run: bool | None = False


def crawlers_get_crawl_metadata() -> list[CrawlMetadata]:
    """Get a return of metadata schemas for all crawlers from the database"""
    engine = db_connect_sync()

    __query = sql(
        """
        select
            cm.spider_name as name,
            cm.data->>'version' as version,
            cm.data->>'last_crawled' as last_crawled,
            cm.data->>'latest_processed' as last_processed,
            cm.data->>'server_latest' as server_latest,
            cm.data->>'force_run' as force_run
        from crawl_meta cm
        order by last_crawled desc;
    """
    )

    with engine.begin() as conn:
        result = conn.execute(__query)
        _crawler_metas = result.fetchall()

    _crawler_meta_models = [
        CrawlMetadata(
            name=row.name,
            version=row.version,
            last_crawled=row.last_crawled,
            last_processed=row.last_processed,
            server_latest=row.server_latest,
            force_run=row.force_run,
        )
        for row in _crawler_metas
    ]

    return _crawler_meta_models
