from typing import Optional

from pydantic import Field

from .core import BaseConfig

JOIN_QUERY = """ +
    ((extract(minute FROM fs.trading_interval AT TIME ZONE '{timezone}')::int / {interval})::integer
    * interval '{interval} minute')::interval
"""


class TimeInterval(BaseConfig):
    # interval size in minutes
    interval: int = Field(..., description="Interval size in minutes")

    interval_human: str = Field(
        ..., description="Interval size in human length"
    )

    interval_sql: str

    trunc: str

    def get_sql_join(self, timezone="UTC") -> Optional[str]:
        if self.interval >= 60:
            return ""

        return JOIN_QUERY.format(interval=self.interval, timezone=timezone)


class TimeIntervalAPI(BaseConfig):
    interval: int = Field(..., description="Interval size in minutes")
    interval_human: str = Field(
        ..., description="Interval size in human length"
    )


class TimePeriod(BaseConfig):
    period: int = Field(..., description="Period in minutes")

    period_human: str = Field(..., description="Period in human size")

    period_sql: str


class TimePeriodAPI(BaseConfig):
    period: int = Field(..., description="Period in minutes")
    period_human: str = Field(..., description="Period in human size")
