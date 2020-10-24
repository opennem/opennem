from fastapi import HTTPException
from starlette import status

from opennem.core.time import (
    INTERVALS_SUPPORTED,
    PERIODS_SUPPORTED,
    get_interval,
    get_period,
)
from opennem.schema.time import TimeInterval, TimePeriod


def human_to_interval(interval_human: str) -> TimeInterval:
    """
        Parses user supplied intervals like "15M" to TimeInterval
        instances.

    """
    if interval_human not in INTERVALS_SUPPORTED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interval not supported. Select one of: {}".format(
                ", ".join(INTERVALS_SUPPORTED)
            ),
        )

    return get_interval(interval_human)


def human_to_period(period_human: str) -> TimePeriod:
    period_human = period_human.strip()

    if period_human not in PERIODS_SUPPORTED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Period not supported. Select one of: {} not {}".format(
                ", ".join(PERIODS_SUPPORTED), period_human
            ),
        )

    return get_period(period_human)

