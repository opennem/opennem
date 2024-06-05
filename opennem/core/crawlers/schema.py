"""OpenNEM Crawler Definitions"""
from collections.abc import Callable
from datetime import datetime
from enum import Enum

from pydantic import Field

from opennem.core.parsers.aemo.filenames import AEMODataBucketSize
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema


class CrawlerPriority(Enum):
    high = 1
    medium = 5
    low = 10


class CrawlerSchedule(Enum):
    live = "1m"
    frequent = "5m"
    quarter_hour = "15m"
    half_hour = "30m"
    hourly = "1h"
    four_times_a_day = "6h"
    twice_a_day = "12h"
    daily = "1d"


class CrawlerDefinition(BaseConfig):
    """Defines a crawler"""

    version: str = Field(default="2")
    name: str
    url: str | None = None

    # These are v3 fields
    urls: list[str] | None = []
    bucket_size: AEMODataBucketSize | None = None

    active: bool = True
    limit: int | None = None
    filename_filter: str | None = None
    latest: bool = False

    network: NetworkSchema | None = None
    backfill_days: int | None = None
    bulk_insert: bool = Field(default=False)

    priority: CrawlerPriority
    schedule: CrawlerSchedule | None = None
    backoff: int | None = None

    # crawl metadata
    last_crawled: datetime | None = None
    last_processed: datetime | None = None
    server_latest: datetime | None = None

    processor: Callable
    parser: Callable | None = None


class CrawlerSet(BaseConfig):
    """Defines a set of crawlers"""

    crawlers: list[CrawlerDefinition]

    def get_crawler(self, name: str) -> CrawlerDefinition:
        """Get a crawler by name"""
        _crawler_lookup = list(filter(lambda x: x.name == name, self.crawlers))

        if not _crawler_lookup:
            raise Exception(f"Could not find crawler {name}")

        return _crawler_lookup.pop()

    def get_crawlers_by_match(self, match: str, only_active: bool = True) -> list[CrawlerDefinition]:
        """Get crawlers by match"""
        _crawler_lookup = list(filter(lambda x: match in x.name, self.crawlers))

        if only_active:
            _crawler_lookup = list(filter(lambda x: x.active, _crawler_lookup))

        if not _crawler_lookup:
            raise Exception(f"Could not find crawler matching {match}")

        return _crawler_lookup

    def get_crawlers_by_schedule(self, schedule: CrawlerSchedule) -> list[CrawlerDefinition]:
        return sorted(
            filter(lambda x: x.schedule == schedule, self.crawlers),
            key=lambda x: x.priority.value,
        )
