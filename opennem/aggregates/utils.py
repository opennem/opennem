"""Utilities for aggregate methods"""

from datetime import datetime

from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_today_opennem


def get_aggregate_year_range(year: int, network: NetworkSchema = NetworkNEM) -> tuple[datetime, datetime]:
    """Get a date range for a year with end exclusive"""
    tz = network.get_fixed_offset()
    today = get_today_opennem()

    date_min = datetime(year, 1, 1, 0, 0, 0, 0, tzinfo=tz)
    date_max = datetime(year + 1, 1, 1, 0, 0, 0, 0, tzinfo=tz)

    if year == today.year:
        date_max = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)

    return date_min, date_max


def get_aggregate_month_range(year: int, month: int, network: NetworkSchema = NetworkNEM) -> tuple[datetime, datetime]:
    """Get a date range for a month with end exclusive"""
    tz = network.get_fixed_offset()
    today = get_today_opennem()

    date_min = datetime(year, month, 1, 0, 0, 0, 0, tzinfo=tz)

    if month < 12:
        date_max = datetime(year, month + 1, 1, 0, 0, 0, 0, tzinfo=tz)
    else:
        date_max = datetime(year + 1, 1, 1, 0, 0, 0, 0, tzinfo=tz)

    if year == today.year and month == today.month and not date_max.day == 1:
        date_max = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)

    return date_min, date_max


if __name__ == "__main__":
    print(get_aggregate_year_range(2023))
