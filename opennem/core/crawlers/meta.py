"""
OpenNEM Crawler Meta

Gets metadata about crawls from the database
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import SessionLocal
from opennem.db.models.opennem import CrawlMeta

logger = logging.getLogger("opennem.crawler.meta")


class CrawlStatTypes(Enum):
    # version of crawler
    # new version is v2+
    version = "version"

    # last crawl run time
    last_crawled = "last_crawled"

    # latest interval
    latest_interval = "latest_interval"

    # last time it was processed (success on insert)
    latest_processed = "latest_processed"

    # the latest data from the server that was processed
    # ie. on AEMO sites this is the latest dirlisting modified time
    # available
    server_latest = "server_latest"

    # generic data holder for all metadata
    data = "data"


async def crawlers_get_all_meta() -> dict[str, Any]:
    """Get all crawler metadata"""
    crawler_meta_dict = {}

    async with SessionLocal() as session:
        stmt = select(CrawlMeta)
        result = await session.execute(stmt)
        spider_meta = result.scalars().all()

        if not spider_meta:
            return {}

        for spider in spider_meta:
            if not spider.data:
                continue

            crawler_meta_dict[spider.spider_name] = spider.data

    return crawler_meta_dict


async def crawler_get_all_meta(crawler_name: str, session: AsyncSession) -> dict[str, Any] | None:
    """Get crawler metadata by crawler name"""
    stmt = select(CrawlMeta).filter_by(spider_name=crawler_name)
    result = await session.execute(stmt)
    spider_meta = result.scalar_one_or_none()

    if not spider_meta:
        return None

    if not spider_meta.data:
        return None

    return spider_meta.data


async def crawler_get_meta(crawler_name: str, key: CrawlStatTypes) -> str | datetime | None:
    """Crawler get specific stat type from metadata for crawler name"""
    async with SessionLocal() as session:
        stmt = select(CrawlMeta).filter_by(spider_name=crawler_name)
        result = await session.execute(stmt)
        spider_meta = result.scalar_one_or_none()

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


async def crawler_set_meta(crawler_name: str, key: CrawlStatTypes, value: Any) -> None:
    """Set a crawler metadata stat type by name — single session, no nesting"""
    async with SessionLocal() as session:
        stmt = select(CrawlMeta).filter_by(spider_name=crawler_name)
        result = await session.execute(stmt)
        spider_meta = result.scalar_one_or_none()

        if not spider_meta:
            spider_meta = CrawlMeta(spider_name=crawler_name, data={})

        if isinstance(value, datetime):
            value = value.isoformat()

        # check server_latest monotonicity within the same session (no nested session)
        if key == CrawlStatTypes.server_latest and spider_meta.data:
            current_raw = spider_meta.data.get(key.value)
            if current_raw:
                try:
                    if datetime.fromisoformat(current_raw) >= datetime.fromisoformat(value):
                        return None
                except (TypeError, ValueError):
                    logger.error(f"Error comparing server_latest: {current_raw} vs {value}")

        spider_meta.data[key.value] = value

        logger.debug(f"Spider {crawler_name} meta: Set {key.value} to {value}")

        session.add(spider_meta)
        await session.commit()


async def crawler_set_meta_many(crawler_name: str, updates: dict[CrawlStatTypes, Any]) -> None:
    """Batch-set multiple crawler metadata keys in a single session + commit"""
    if not updates:
        return

    async with SessionLocal() as session:
        stmt = select(CrawlMeta).filter_by(spider_name=crawler_name)
        result = await session.execute(stmt)
        spider_meta = result.scalar_one_or_none()

        if not spider_meta:
            spider_meta = CrawlMeta(spider_name=crawler_name, data={})

        if not spider_meta.data:
            spider_meta.data = {}

        for key, value in updates.items():
            if isinstance(value, datetime):
                value = value.isoformat()

            # check server_latest monotonicity
            if key == CrawlStatTypes.server_latest:
                current_raw = spider_meta.data.get(key.value)
                if current_raw:
                    try:
                        if datetime.fromisoformat(current_raw) >= datetime.fromisoformat(value):
                            continue
                    except (TypeError, ValueError):
                        logger.error(f"Error comparing server_latest: {current_raw} vs {value}")

            spider_meta.data[key.value] = value

        session.add(spider_meta)
        await session.commit()

        logger.debug(f"Spider {crawler_name} meta: batch set {list(updates.keys())}")


if __name__ == "__main__":
    import asyncio

    async def main():
        # await crawler_set_meta("au.nem.latest.dispatch_scada", CrawlStatTypes.last_crawled, datetime.now())
        print(await crawlers_get_all_meta())

    asyncio.run(main())
