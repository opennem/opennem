"""
Unit tests for date utils in opennem.utils.dates

"""
from datetime import datetime, timedelta

import datedelta
import pytest

from opennem.utils.dates import num_intervals_between_datetimes


@pytest.mark.parametrize(
    ["interval", "date_start", "date_end", "expected"],
    [
        (
            timedelta(minutes=5),
            datetime.fromisoformat("2022-01-01T00:00:00"),
            datetime.fromisoformat("2022-01-01T01:00:00"),
            13,
        ),
        # tz aware
        (
            timedelta(minutes=5),
            datetime.fromisoformat("2022-01-01T00:00:00+10:00"),
            datetime.fromisoformat("2022-01-01T01:00:00+10:00"),
            13,
        ),
        # days
        (
            timedelta(days=1),
            datetime.fromisoformat("2022-01-01T00:00:00"),
            datetime.fromisoformat("2022-01-05T00:00:00"),
            5,
        ),
        # months
        (
            datedelta.MONTH,
            datetime.fromisoformat("2022-01-01T00:00:00"),
            datetime.fromisoformat("2022-05-01T00:00:00"),
            5,
        ),
    ],
)
def test_date_diff(interval: timedelta, date_start: datetime, date_end: datetime, expected: int) -> None:
    subject_number_of_intervals = num_intervals_between_datetimes(interval, date_start, date_end)
    assert subject_number_of_intervals == expected, "Got the expected number of intervals between dates"
