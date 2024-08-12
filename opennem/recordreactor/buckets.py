"""
This module provides utility functions for working with buckets in the context of recordreactor.

"""

from datetime import datetime, timedelta

# supported bucket sizes for recordrecor queries. must be supported by the database date_part function
BUCKET_SIZES: list[str] = ["interval", "day", "week", "month", "year"]


def is_end_of_period(dt: datetime, bucket_size: str) -> bool:
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
    if bucket_size not in BUCKET_SIZES:
        raise ValueError(f"Invalid bucket_size: {bucket_size}")

    if bucket_size == "interval":
        return True
    elif bucket_size == "day":
        return dt.hour == 0 and dt.minute == 0 and dt.second == 0
    elif bucket_size == "week":
        return dt.weekday() == 0 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
    elif bucket_size == "month":
        return dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
    elif bucket_size == "year":
        return dt.month == 1 and dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0
    return False


def get_period_start_end(dt: datetime, bucket_size: str) -> tuple[datetime, datetime]:
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
    if bucket_size not in BUCKET_SIZES:
        raise ValueError(f"Invalid bucket_size: {bucket_size}")

    start, end = None, None

    if bucket_size == "interval":
        return dt, dt
    elif bucket_size == "day":
        # day returns midnight this morning and end of current day
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return start - timedelta(days=1), start
    elif bucket_size == "week":
        # week returns monday this week at midnight and end of current week at midnight
        start = (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return start - timedelta(days=7), start
    elif bucket_size == "month":
        start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if start.month == 1:
            return start.replace(year=start.year - 1, month=12), start
        return start.replace(month=start.month - 1), start
    elif bucket_size == "year":
        start = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return start.replace(year=start.year - 1), start
    else:
        raise ValueError(f"Invalid bucket_size: {bucket_size}")

    return start, end


def get_bucket_sql(bucket_size: str, field_name: str | None = None, extra: str = "") -> str:
    """
    Method to get the SQL expression for a given bucket size.

    Args:
        bucket_size (str): The bucket size to get the SQL expression for.

    Returns:
        str: The SQL expression for the given bucket size.

    Raises:
        ValueError: If the bucket_size is not valid.
    """
    if bucket_size not in BUCKET_SIZES:
        raise ValueError(f"Invalid bucket_size: {bucket_size}")

    if not field_name:
        field_name = "interval"

    if bucket_size == "interval":
        return "trading_interval"

    return f"time_bucket_gapfill('1 {bucket_size}', {field_name} {extra})"


def get_bucket_interval(bucket_size: str, interval_size: int = 5) -> str:
    """
    Method to get the interval for a given bucket size.

    Args:
        bucket_size (str): The bucket size to get the interval for.

    Returns:
        str: The interval for the given bucket size.

    Raises:
        ValueError: If the bucket_size is not valid.
    """
    if bucket_size not in BUCKET_SIZES:
        raise ValueError(f"Invalid bucket_size: {bucket_size}")

    if bucket_size == "interval":
        return f"{interval_size} minutes"

    return f"1 {bucket_size}"
