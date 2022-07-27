"""" Reads and stores crawler history """
import logging
from dataclasses import dataclass, field
from datetime import datetime
from textwrap import dedent

from sqlalchemy import text as sql

from opennem.core.time import get_interval
from opennem.db import get_database_engine, get_scoped_session
from opennem.db.models.opennem import CrawlHistory
from opennem.schema.time import TimeInterval

logger = logging.getLogger("opennem.crawler.history")


@dataclass
class CrawlHistoryEntry:
    interval: datetime
    records: int | None = field(default=None)


@dataclass
class CrawlHistoryGap:
    interval: datetime


def set_crawler_history(crawler_name: str, histories: list[CrawlHistoryEntry]) -> int:
    """Sets the crawler history"""
    engine = get_database_engine()

    date_max = max([i.interval for i in histories])
    date_min = min([i.interval for i in histories])

    logger.debug(f"date_max and date_max: {date_max}, {date_min}")

    stmt = sql(
        """
        select
            interval
        from crawl_history
        where
            interval >= :date_max
            and interval <= :date_min
    """
    )

    query = stmt.bindparams(date_max=date_max, date_min=date_min)

    with engine.connect() as c:
        results = list(c.execute(query))

    existing_intervals = [i[0] for i in results]

    logger.debug(f"Got {len(existing_intervals)} existing intervals")

    with get_scoped_session() as session:
        for ch in histories:
            if ch.interval in existing_intervals:
                continue

            model = CrawlHistory(
                source="nemweb",
                crawler_name=crawler_name,
                interval=ch.interval,
                inserted_records=ch.records,
                network_id="NEM",
            )
            session.add(model)

        session.commit()

    return len(histories)


def get_crawler_history(crawler_name: str, interval: TimeInterval, days: int = 3) -> list[datetime]:
    """Gets the crawler history"""
    engine = get_database_engine()

    stmt = sql(
        """
        select
            t.trading_interval at time zone 'AEST' as interval,
            t.has_record
        from
        (
            select
                time_bucket_gapfill(:bucket_size, ch.interval) as trading_interval,
                ch.crawler_name,
                coalesce(sum(ch.inserted_records), 0) as records_inserted,
                case when sum(ch.inserted_records) is NULL then FALSE else TRUE end as has_record
            from crawl_history ch
            where
                ch.interval >= now() at time zone 'AEST' - interval :days
                and ch.interval <= now()
                and ch.crawler_name = :crawler_name
            group by 1, 2
        ) as t
        where
            t.has_record is FALSE
        order by 1 desc;
    """
    )

    query = stmt.bindparams(crawler_name=crawler_name, bucket_size=interval.interval_sql, days=f"{days} days")

    logger.debug(dedent(str(query)))

    with engine.connect() as c:
        results = list(c.execute(query))

    models = [i[0] for i in results]

    return models


def get_crawler_missing_intervals(
    crawler_name: str,
    interval_size: TimeInterval,
    days: int = 365 * 3,
) -> list[datetime]:
    """Gets the crawler missing intervals going back a period of days"""
    engine = get_database_engine()

    stmt = sql(
        """
        with intervals as (
            select
                interval
            from generate_series(nemweb_latest_interval() - interval :days, nemweb_latest_interval(), interval  :interval_size) AS interval
        )

        select
            intervals.interval,
            case when ch.inserted_records is NULL then FALSE else TRUE end as has_record
        from intervals
        left join (
            select * from crawl_history
            where crawler_name = :crawler_name
            and interval <= nemweb_latest_interval() and interval >= nemweb_latest_interval() - interval :days
        ) as ch on ch.interval = intervals.interval
        where ch.inserted_records is null
        order by 1 desc;
    """
    )

    query = stmt.bindparams(crawler_name=crawler_name, days=f"{days} days", interval_size=f"{interval_size} minutes")

    logger.debug(dedent(str(query)))

    with engine.connect() as c:
        results = list(c.execute(query))

    models = [i[0] for i in results]

    return models


if __name__ == "__main__":
    m = get_crawler_missing_intervals("au.nemweb.trading_is", interval_size=get_interval("1M"))
    for i in m:
        print(i)
