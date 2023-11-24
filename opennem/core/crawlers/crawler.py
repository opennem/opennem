"""Get crawl metadata info from storage

"""

import logging
from datetime import datetime
from textwrap import dedent

from opennem.db import get_database_engine
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
    engine = get_database_engine()

    __query = """
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
    _crawler_metas = []

    with engine.connect() as c:
        _crawler_metas = list(c.execute(__query))

    if not _crawler_metas:
        return []

    _crawler_meta_models = [CrawlMetadata(**i) for i in _crawler_metas]

    return _crawler_meta_models


def crawlers_flush_metadata(days: int | None = None, crawler_name: str | None = None) -> None:
    """Flush the crawler metadata"""
    engine = get_database_engine()

    __meta_query = """
        delete
        from crawl_meta cm
        where
            1=1 and
            {crawler_clause}
        ;
    """

    meta_crawler_clause = ""

    if crawler_name:
        meta_crawler_clause = crawler_name

    meta_query = __meta_query.format(
        crawler_clause=f"spider_name = '{meta_crawler_clause}'",
    )

    __history_query = """
        delete
        from crawl_history
        where
            1=1 and
            {crawler_clause_history}
            {days_clause_history}

    """

    crawler_clause_history = ""

    if crawler_name:
        crawler_clause_history = f"crawler_name = '{crawler_name}' and"

    days_clause_history = ""

    if days:
        days_clause_history = f"interval >= now() - interval '{days} days'"

    history_query = __history_query.format(crawler_clause_history=crawler_clause_history, days_clause_history=days_clause_history)

    logger.debug(dedent(meta_query))
    logger.debug(dedent(history_query))

    with engine.connect() as c:
        c.execute(meta_query)
        c.execute(history_query)


# debug entry point
if __name__ == "__main__":
    metas = crawlers_get_crawl_metadata()

    for m in metas:
        logger.info(f"{m.name} {m.version} {m.last_crawled} {m.last_processed} {m.server_latest}")
