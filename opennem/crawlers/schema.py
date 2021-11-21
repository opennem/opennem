"""OpenNEM Crawler Definitions"""
from datetime import datetime
from enum import Enum
from typing import Callable, List, Optional

from opennem.schema.core import BaseConfig


class CrawlerPriority(Enum):
    high = 1
    medium = 5
    low = 10


class CrawlerSchedule(Enum):
    live = "1m"
    frequent = "5m"
    hourly = "1h"
    daily = "1d"


class CrawlerDefinition(BaseConfig):
    """Defines a crawler"""

    name: str
    url: Optional[str]
    limit: Optional[int]
    filename_filter: Optional[str]

    priority: CrawlerPriority
    schedule: Optional[CrawlerSchedule]

    # crawl metadata
    last_crawled: Optional[datetime]
    last_processed: Optional[datetime]

    processor: Callable


class CrawlerSet(BaseConfig):
    """Defines a set of crawlers"""

    crawlers: List[CrawlerDefinition]

    def get_crawler(self, name: str) -> CrawlerDefinition:
        """Get a crawler by name"""
        _crawler_lookup = list(filter(lambda x: x.name == name, self.crawlers))

        if not _crawler_lookup:
            raise Exception(f"Could not find crawler {name}")

        return _crawler_lookup.pop()

    def get_crawlers_by_schedule(self, schedule: CrawlerSchedule) -> List[CrawlerDefinition]:
        return list(
            sorted(
                filter(lambda x: x.schedule == schedule, self.crawlers),
                key=lambda x: x.priority.value,
            )
        )
