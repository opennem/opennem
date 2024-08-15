"""
This module provides utility functions for working with buckets in the context of recordreactor.

"""

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from opennem.recordreactor.schema import MilestonePeriod
from opennem.schema.network import NetworkSchema


def is_end_of_period(dt: datetime, bucket_size: MilestonePeriod) -> bool:
    """
    Method to check if a given datetime is the end of a period for a given bucket size.

    Args:
        dt (datetime): The datetime to check.
        bucket_size (str): The bucket size to check.

    Returns:
        bool: True if the datetime is the end of a period, False otherwise.

    Raises:
        ValueError: If the bucket_size is not valid.
    """
    match bucket_size:
        case MilestonePeriod.interval:
            return True
        case MilestonePeriod.day:
            return dt.hour == 0 and dt.minute == 0 and dt.second == 0
        case MilestonePeriod.week:
            return dt.weekday() == 0 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
        case MilestonePeriod.month:
            return dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
        case MilestonePeriod.quarter:
            return dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.month in [1, 4, 7, 10]
        case MilestonePeriod.season:
            return dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0 and dt.month in [3, 6, 9, 12]
        case MilestonePeriod.year:
            return dt.month == 1 and dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
        case MilestonePeriod.financial_year:
            return dt.month == 7 and dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
        case _:
            raise ValueError(f"Invalid bucket_size: {bucket_size}")


def get_period_start_end(dt: datetime, bucket_size: MilestonePeriod, network: NetworkSchema) -> tuple[datetime, datetime]:
    """
    Method to get the start and end of the most recent completed period for a given datetime and bucket size.

    Args:
        dt (datetime): The datetime to get the period for.
        bucket_size (str): The bucket size to get the period for.

    Returns:
        tuple[datetime, datetime]: The start and end of the most recent completed period.

    Raises:
        ValueError: If the bucket_size is not valid.
    """

    match bucket_size:
        case MilestonePeriod.interval:
            return dt, dt + timedelta(minutes=network.interval_size)
        case MilestonePeriod.day:
            # day returns midnight this morning and end of current day
            start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return start - timedelta(days=1), start
        case MilestonePeriod.week:
            # week returns monday this week at midnight and end of current week at midnight
            start = (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            return start - timedelta(days=7), start
        case MilestonePeriod.month:
            start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 1:
                return start.replace(year=start.year - 1, month=12), start
            return start - relativedelta(months=1), start
        case MilestonePeriod.season | MilestonePeriod.quarter:
            start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start - relativedelta(months=3), start
        case MilestonePeriod.year:
            start = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return start.replace(year=start.year - 1), start
        case MilestonePeriod.financial_year:
            start = dt.replace(month=7, day=1, hour=0, minute=0, second=0, microsecond=0)
            return start.replace(year=start.year - 1), start
        case _:
            raise ValueError(f"Invalid bucket_size: {bucket_size}")


def get_bucket_interval(bucket_size: MilestonePeriod, interval_size: int = 5) -> str:
    """
    Method to get the interval for a given bucket size.

    Args:
        bucket_size (str): The bucket size to get the interval for.

    Returns:
        str: The interval for the given bucket size.

    Raises:
        ValueError: If the bucket_size is not valid.
    """

    if bucket_size.value == "interval":
        return f"{interval_size} minutes"

    return f"1 {bucket_size.value}"
