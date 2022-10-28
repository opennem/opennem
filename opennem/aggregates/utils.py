""" Utilities for aggregate methods """
from datetime import datetime

from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_today_opennem


def get_aggregate_year_range(year: int, network: NetworkSchema = NetworkNEM) -> tuple[datetime, datetime]:
    """Get a date range for a year with end exclusive"""
    tz = network.get_fixed_offset()

    date_min = datetime(year, 1, 1, 0, 0, 0, 0, tzinfo=tz)
    date_max = datetime(year + 1, 1, 1, 0, 0, 0, 0, tzinfo=tz)

    if year == get_today_opennem().year:
        date_max = datetime.now().replace(hour=0, minute=0, second=0, tzinfo=tz)

    return date_min, date_max
