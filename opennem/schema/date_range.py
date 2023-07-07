from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawlDateRange:
    start: datetime
    end: datetime
