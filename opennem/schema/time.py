from datetime import timedelta
from typing import Optional

from pydantic import Field

from opennem.utils.time import human_to_timedelta

from .core import BaseConfig

JOIN_QUERY = """ +
    ((extract(minute FROM fs.{field} AT TIME ZONE '{timezone}')::int / {interval})::integer
    * interval '{interval} minute')::interval
"""


class TimeInterval(BaseConfig):
    # interval size in minutes
    interval: int = Field(..., description="Interval size in minutes")

    interval_human: str = Field(..., description="Interval size in human length")

    interval_sql: str

    trunc: str

    def get_sql_join(self, field="trading_interval", timezone="UTC") -> Optional[str]:
        if self.interval >= 60:
            return ""

        return JOIN_QUERY.format(interval=self.interval, field=field, timezone=timezone)

    def get_timedelta(self) -> timedelta:
        return human_to_timedelta(self.interval_human)


class TimeIntervalAPI(BaseConfig):
    interval: int = Field(..., description="Interval size in minutes")
    interval_human: str = Field(..., description="Interval size in human length")


class TimePeriod(BaseConfig):
    period: int = Field(..., description="Period in minutes")

    period_human: str = Field(..., description="Period in human size")

    period_sql: str


class TimePeriodAPI(BaseConfig):
    period: int = Field(..., description="Period in minutes")
    period_human: str = Field(..., description="Period in human size")
