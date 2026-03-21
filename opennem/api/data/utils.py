"""
Utility functions for the OpenNEM API v4 data endpoints.

This module contains shared utility functions for data validation and processing.
"""

from datetime import datetime, timedelta
from typing import NoReturn

from fastapi import HTTPException

from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkSchema
from opennem.users.plans import BUCKET_LIMITS_ADMIN, OpenNEMPlan, get_max_interval_days_for_plan, get_plan_config
from opennem.users.schema import OpenNEMUser
from opennem.utils.dates import get_last_completed_interval_for_network


def _raise_invalid_date_range(interval: Interval, max_days: int) -> NoReturn:
    raise HTTPException(
        status_code=400,
        detail=f"Date range too large for {interval.value} interval. Maximum range is {max_days} days.",
    )


def get_max_interval_days(interval: Interval, user: OpenNEMUser | None = None) -> int:
    """Get the maximum allowed days for a given interval based on user's plan."""
    if user and user.is_admin:
        return BUCKET_LIMITS_ADMIN.get(interval, 10_000)

    if user:
        return get_max_interval_days_for_plan(user.plan, interval)

    return get_max_interval_days_for_plan(OpenNEMPlan.COMMUNITY, interval)


def validate_date_range(
    network: NetworkSchema, interval: Interval, user: OpenNEMUser | None, date_start: datetime | None, date_end: datetime | None
) -> tuple[datetime, datetime]:
    """Validate that the date range is appropriate for the given interval and user plan."""

    if date_start and date_start.tzinfo is not None:
        raise HTTPException(status_code=400, detail="Date start must be timezone naive and in network time")

    if date_end and date_end.tzinfo is not None:
        raise HTTPException(status_code=400, detail="Date end must be timezone naive and in network time")

    # Get default dates if not provided
    if date_end is None:
        date_end = get_last_completed_interval_for_network(network=network, tz_aware=False)

    if date_start is None:
        date_start = get_default_start_date(interval, date_end)

    max_days = get_max_interval_days(interval, user)

    try:
        date_range = date_end - date_start
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid dates passed") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid date range") from e

    if date_range.days > max_days:
        _raise_invalid_date_range(interval, max_days)

    # Period limit — restrict how far back date_start can be
    plan = user.plan if user else OpenNEMPlan.COMMUNITY
    period_limit = get_plan_config(plan).period_limit_days
    if not (user and user.is_admin) and period_limit != -1:
        earliest = datetime.now() - timedelta(days=period_limit)
        if date_start < earliest:
            raise HTTPException(
                status_code=400,
                detail=f"Date start is too far in the past. Your plan allows data from the last {period_limit} days.",
            )

    return date_start, date_end


def get_default_start_date(interval: Interval, date_end: datetime) -> datetime:
    """Get the default start date for a given interval (half of max for anonymous)."""
    return date_end - timedelta(days=get_max_interval_days(interval) / 2)
