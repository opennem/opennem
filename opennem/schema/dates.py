"""
OpenNEM Time Series Schema

Defines a tiem series and methods to extract start and end times based on max/min from
SCADA or other ranes and the start/end used in SQL queries

All ranges and queries are _inclusive_ of start/end dates

End is the most recent time chronoligally ordered:

[start] === series === [end]

"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional, Union

from datetime_truncate import truncate as date_trunc

from opennem.api.time import human_to_interval, human_to_period
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.dates import get_end_of_last_month
from opennem.utils.interval import get_human_interval
from opennem.utils.version import CUR_YEAR


def valid_trunc(trunc: str) -> str:
    get_human_interval(trunc)
    return trunc


class DatetimeRange(BaseConfig):
    """Sime start/end date used for sql queries"""

    start: datetime

    # Alias last
    end: datetime

    interval: TimeInterval

    @property
    def trunc(self) -> str:
        return self.interval.interval_human

    @property
    def length(self) -> int:
        """Return the number of buckets in the range"""
        _comp = self.start
        _delta = get_human_interval(self.trunc)
        count = 1

        while _comp <= self.end:
            _comp += _delta
            count += 1

        return count


class TimeSeries(BaseConfig):
    """A time series. Consisting of a start and
    end date (inclusive), a bucket size, timezone info
    and methods to extract DatetimeRange's for sql queries
    """

    # Start and end dates
    start: datetime
    end: datetime

    # The network for this date range
    # used for timezone and offsets
    network: NetworkSchema

    # The interval which provides the bucket size
    interval: TimeInterval

    # The length of the series to extract
    period: TimePeriod

    # extract a particular year
    year: Optional[int]

    # Forecast means the time series goes forward from now
    forecast: bool = False

    # Default forward forecast time period
    forecast_period: str = "7d"

    def get_range(self) -> DatetimeRange:
        """Return a DatetimeRange from the time series for queries"""
        start = self.start
        end = self.end

        # If its a forward looking forecast
        # jump out early
        if self.forecast:
            start = self.end + timedelta(minutes=self.interval.interval)
            end = self.end + get_human_interval(self.forecast_period)

            start = start.astimezone(self.network.get_fixed_offset())
            end = end.astimezone(self.network.get_fixed_offset())

            return DatetimeRange(start=start, end=end, interval=self.interval)

        # subtract the period (ie. 7d from the end for start if not all)
        if self.period == human_to_period("all"):
            start = date_trunc(start, self.interval.trunc)
            start = start.replace(
                hour=0, minute=0, second=0, tzinfo=self.network.get_fixed_offset()
            )

            # If its all per month take the end of the last month
            if self.interval == human_to_interval("1M"):
                end = date_trunc(get_end_of_last_month(end), "day")
                end = end.replace(
                    hour=23, minute=59, second=59, tzinfo=self.network.get_fixed_offset()
                )

            self.year = None

        else:
            start = self.end - get_human_interval(self.period.period_human)

        if self.year:
            if self.year > end.year:
                raise Exception("Specified year is great than end year")

            start = start.replace(
                year=self.year,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=self.network.get_fixed_offset(),
            )
            # start = date_trunc(start, self.interval.trunc)

            if self.year != CUR_YEAR:
                end = datetime(
                    year=self.year,
                    month=12,
                    day=31,
                    hour=23,
                    minute=59,
                    second=59,
                    tzinfo=self.network.get_fixed_offset(),
                )
            else:
                today = datetime.now(tz=self.network.get_fixed_offset())
                end = datetime(
                    year=CUR_YEAR, month=today.month, day=today.day, hour=23, minute=59, second=59
                )
                end = end - timedelta(days=1)
                end = end.replace(tzinfo=self.network.get_fixed_offset())

                if self.end < today:
                    end = self.end

        # localize times
        if not start.tzinfo or start.tzinfo != self.network.get_fixed_offset():
            start = start.astimezone(self.network.get_fixed_offset())

        if not end.tzinfo or end.tzinfo != self.network.get_fixed_offset():
            end = end.astimezone(self.network.get_fixed_offset())

        # if start.tzinfo != self.network.get_fixed_offset():
        #     start = start.replace(tzinfo=self.network.get_fixed_offset())

        # if end.tzinfo != self.network.get_fixed_offset():
        #     end = end.replace(tzinfo=self.network.get_fixed_offset())

        dtr = DatetimeRange(start=start, end=end, interval=self.interval)

        return dtr
