"""
OpenNEM Time Series Schema

Defines a tiem series and methods to extract start and end times based on max/min from
SCADA or other ranes and the start/end used in SQL queries

All ranges and queries are _inclusive_ of start/end dates

End is the most recent time chronoligally ordered:

[start] === series === [end]

"""

from __future__ import annotations

import enum
from datetime import date, datetime, timedelta

from datetime_truncate import truncate as date_trunc

from opennem.api.time import human_to_interval, human_to_period
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.utils.dates import get_end_of_last_month, get_today_opennem
from opennem.utils.interval import get_human_interval
from opennem.utils.timezone import is_aware


def valid_trunc(trunc: str) -> str:
    get_human_interval(trunc)
    return trunc


class StatType(enum.Enum):
    power = "power"
    energy = "energy"
    interchange = "interchange"
    marketvalue = "market_value"
    emissions = "emissions"
    gov = "gov"


class ExportDatetimeRange(BaseConfig):
    """Sime start/end date used for sql queries"""

    start: datetime

    # Alias last
    end: datetime

    interval: TimeInterval

    year: int | None = None

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


class OpennemExportSeries(BaseConfig):
    """An export series, consisting of date range, a bucket size, timezone info
    and methods to extract DatetimeRange's for sql queries
    """

    start: datetime
    end: datetime = datetime.now()

    # The network for this date range
    # used for timezone and offsets
    network: NetworkSchema

    # The interval which provides the bucket size
    interval: TimeInterval

    # The length of the series to extract
    period: TimePeriod | None = None

    # extract a particular year
    year: int | None = None

    # extract a particular month
    month: date | None = None

    # Forecast means the time series goes forward from now
    forecast: bool = False

    # Default forward forecast time period
    forecast_period: str = "7d"

    def __str__(self) -> str:
        """Return an informative stringified object for debugging and exceptions"""
        return (
            f"Network {self.network.code} at interval {self.interval.interval_human} and "
            f"period {self.period.period_human if self.period else None} between {self.start} and {self.end}"
        )

    def get_range(self) -> ExportDatetimeRange:
        """Return a DatetimeRange from the time series for queries"""
        start = self.start
        end = self.end

        # @TODO do a proper time trim method
        if self.interval.interval == 30:
            replace_min_start = 30 if start.minute >= 30 else 0
            replace_min_end = 30 if end.minute >= 30 else 0

            start = start.replace(minute=replace_min_start, second=0, microsecond=0)
            end = end.replace(minute=replace_min_end, second=0, microsecond=0)

        # If its a forward looking forecast
        # jump out early
        if self.forecast:
            # add an interval since we do < in queries
            forecast_start = end
            forecast_end = forecast_start + get_human_interval(self.forecast_period)

            if not is_aware(forecast_start):
                forecast_start = forecast_start.astimezone(self.network.get_fixed_offset())
            if not is_aware(forecast_end):
                forecast_end = forecast_end.astimezone(self.network.get_fixed_offset())

            return ExportDatetimeRange(start=forecast_start, end=forecast_end, interval=self.interval)

        # subtract the period (ie. 7d from the end for start if not all)
        if self.period == human_to_period("all"):
            start = date_trunc(start, self.interval.trunc)
            start = start.replace(hour=0, minute=0, second=0, tzinfo=self.network.get_fixed_offset())

            # If its all per month take the end of the last month
            if self.interval == human_to_interval("1M"):
                end = date_trunc(get_end_of_last_month(end), "day")
                end = end.replace(hour=23, minute=59, second=59, tzinfo=self.network.get_fixed_offset())

            self.year = None

        elif self.period:
            start = self.end - get_human_interval(self.period.period_human)

            # trim again
            if self.interval.interval == 30:
                replace_min_start = 30 if start.minute >= 30 else 0
                start = start.replace(minute=replace_min_start, second=0, microsecond=0)

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

            end = datetime(
                year=self.year,
                month=12,
                day=31,
                hour=23,
                minute=59,
                second=59,
                tzinfo=self.network.get_fixed_offset(),
            )

            current_year = get_today_opennem().year

            if self.year == current_year:
                end = datetime(
                    year=current_year,
                    month=self.end.month,
                    day=self.end.day,
                    hour=23,
                    minute=59,
                    second=59,
                )

                end = end - timedelta(days=1)

                end = end.replace(tzinfo=self.network.get_fixed_offset())

        if self.month:
            start = datetime(
                year=self.month.year,
                month=self.month.month,
                day=1,
                hour=0,
                minute=0,
                second=0,
                tzinfo=self.network.get_fixed_offset(),
            )

            end = start + get_human_interval("1M") - timedelta(days=1)

            end = end.replace(
                hour=23,
                minute=59,
                second=59,
            )

        # localize times
        if not is_aware(start):
            start = start.astimezone(self.network.get_fixed_offset())
        if not is_aware(end):
            end = end.astimezone(self.network.get_fixed_offset())

        return ExportDatetimeRange(start=start, end=end, interval=self.interval)
