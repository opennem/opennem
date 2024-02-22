"""" Reads and stores crawler history """
import logging
from dataclasses import dataclass, field
from datetime import datetime
from textwrap import dedent

from datetime_truncate import truncate as date_trunc
from sqlalchemy import text as sql
from sqlalchemy.dialects.postgresql import insert

from opennem.core.time import get_interval
from opennem.db import get_database_engine, get_scoped_session
from opennem.db.models.opennem import CrawlHistory
from opennem.schema.time import TimeInterval
from opennem.utils.dates import get_today_opennem

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
    session = get_scoped_session()

    history_intervals = [i.interval for i in histories]

    logger.debug(f"Have {len(history_intervals)} history intervals for {crawler_name}")

    date_max = max(history_intervals)
    date_min = min(history_intervals)

    logger.debug(f"crawler {crawler_name} date range: {date_min}, {date_max}")

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

    logger.debug(f"Got {len(existing_intervals)} existing intervals for crawler {crawler_name}")

    # Persist the crawl history records
    crawl_history_records: list[dict[str, datetime | str | int | None]] = []

    for ch in histories:
        crawl_history_records.append(
            {
                "source": "nemweb",
                "crawler_name": crawler_name,
                "network_id": "NEM",
                "interval": ch.interval,
                "inserted_records": ch.records,
                "crawled_time": None,
                "processed_time": get_today_opennem(),
            }
        )

    # insert
    stmt = insert(CrawlHistory).values(crawl_history_records)
    stmt.bind = engine  # type: ignore
    stmt = stmt.on_conflict_do_update(  # type: ignore
        index_elements=["source", "crawler_name", "network_id", "interval"],
        set_={
            "inserted_records": stmt.excluded.inserted_records,  # type: ignore
            "crawled_time": stmt.excluded.crawled_time,  # type: ignore
            "processed_time": stmt.excluded.processed_time,  # type: ignore
        },
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error(f"set_crawler_history error updating records: {e}")
    finally:
        session.rollback()
        session.close()
        engine.dispose()

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
                ch.interval >= now() at time zone 'AEST' - interval '3 days'
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
    interval: TimeInterval,
    days: int = 14,
) -> list[datetime]:
    """Gets the crawler missing intervals going back a period of days

    :param crawler_name: The crawler name
    :param interval: The interval to check
    :param days: The number of days to check back
    """
    engine = get_database_engine()

    stmt = sql(
        f"""
        with intervals as (
            select
                interval
            from generate_series(
                nemweb_latest_interval() - interval '14 days',
                nemweb_latest_interval(),
                interval '{interval.interval_sql} minutes'
            ) AS interval
        )

        select
            intervals.interval,
            case when ch.inserted_records is NULL then FALSE else TRUE end as has_record
        from intervals
        left join (
            select * from crawl_history
            where crawler_name = :crawler_name
            and interval <= nemweb_latest_interval() and interval >= nemweb_latest_interval() - interval '14 days'
        ) as ch on ch.interval = intervals.interval
        where ch.inserted_records is null
        order by 1 desc;
    """
    )

    if not days or not isinstance(days, int):
        raise Exception("Days is required and should be an int")

    query = stmt.bindparams(crawler_name=crawler_name)

    with engine.connect() as c:
        results = list(c.execute(query))

    models = [i[0] for i in results]

    # truncate
    # @NOTE specific >= as we trunc hour or greater
    if interval.interval >= 60:
        models = [date_trunc(i, interval.trunc) for i in models]

    logger.debug(f"Got {len(models)} missing intervals for crawler {crawler_name}")

    return models


if __name__ == "__main__":
    m = get_crawler_missing_intervals("au.nemweb.current.trading_is", interval=get_interval("5m"), days=3)
    for i in m[:5]:
        print(i)
