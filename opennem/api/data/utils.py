"""
Utility functions for the OpenNEM API v4 data endpoints.

This module contains shared utility functions for data validation and processing.
"""

from datetime import datetime, timedelta
from typing import NoReturn

from fastapi import HTTPException

from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkSchema
from opennem.utils.dates import get_last_completed_interval_for_network


def _raise_invalid_date_range(interval: Interval, max_days: int) -> NoReturn:
    """
    Raise an HTTP error for invalid date ranges.

    Args:
        interval: The interval being queried
        max_days: Maximum allowed days for the interval

    Raises:
        HTTPException: Always raised with a descriptive message
    """
    raise HTTPException(
        status_code=400,
        detail=f"Date range too large for {interval.value} interval. Maximum range is {max_days} days.",
    )


def get_max_interval_days(interval: Interval) -> int:
    """
    Get the maximum allowed days for a given interval.

    Args:
        interval: The interval to get max days for

    Returns:
        int: Maximum number of days allowed for the interval
    """
    # Define maximum days for each interval
    MAX_INTERVAL_DAYS = {
        Interval.INTERVAL: 7,  # 5m intervals max 7 days
        Interval.HOUR: 30,  # 1h intervals max 30 days
        Interval.DAY: 365,  # 1d intervals max 1 year
        Interval.WEEK: 365,  # 7d intervals max 1 year
        Interval.MONTH: 730,  # 1M intervals max 2 years
        Interval.QUARTER: 1825,  # 3M intervals max 5 years
        Interval.SEASON: 1825,  # Season intervals max 5 years
        Interval.YEAR: 3650,  # 1y intervals max 5 years
    }

    return MAX_INTERVAL_DAYS.get(interval, 7)  # Default to 7 days for unknown intervals


def validate_date_range(
    network: NetworkSchema, interval: Interval, date_start: datetime | None, date_end: datetime | None
) -> tuple[datetime, datetime]:
    """
    Validate that the date range is appropriate for the given interval.

    This function checks if the date range exceeds the maximum allowed days
    for the specified interval. If the range is too large, it raises an
    HTTPException.

    Args:
        interval: The interval being queried
        date_start: Start date of the range
        date_end: End date of the range

    Raises:
        HTTPException: If the date range is too large for the interval
    """

    if date_start and date_start.tzinfo is not None:
        raise HTTPException(status_code=400, detail="Date start must be timezone naive and in network time")

    if date_end and date_end.tzinfo is not None:
        raise HTTPException(status_code=400, detail="Date end must be timezone naive and in network time")

    # Get default dates if not provided
    if date_end is None:
        date_end = get_last_completed_interval_for_network(network=network, tz_aware=False)

    if date_start is None:
        date_start = get_default_start_date(interval, date_end)

    max_days = get_max_interval_days(interval)

    try:
        date_range = date_end - date_start
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid dates passed") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid date range") from e

    if date_range.days > max_days:
        _raise_invalid_date_range(interval, max_days)

    return date_start, date_end


def get_default_start_date(interval: Interval, date_end: datetime) -> datetime:
    """
    Get the default start date for a given interval.

    The start date is based on the interval and the end date.

    It is derived from get_max_interval_days and is half the maximum value.
    """
    return date_end - timedelta(days=get_max_interval_days(interval) / 2)
