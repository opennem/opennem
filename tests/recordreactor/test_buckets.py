from datetime import datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from opennem.recordreactor.utils.buckets import BUCKET_SIZES, get_bucket_sql, get_period_start_end, is_end_of_period


# is_end_of_period tests
def test_is_end_of_period_interval():
    dt = datetime(2023, 6, 15, 12, 30)
    assert is_end_of_period(dt, "interval") == True  # noqa: E712


@pytest.mark.parametrize(
    "dt,expected",
    [
        (datetime(2023, 6, 16, 0, 0, 0), True),
        (datetime(2023, 6, 15, 23, 59, 59), False),
    ],
)
def test_is_end_of_period_day(dt, expected):
    assert is_end_of_period(dt, "day") == expected


@pytest.mark.parametrize(
    "dt,expected",
    [
        (datetime(2023, 6, 19, 0, 0, 0), True),  # Monday
        (datetime(2023, 6, 18, 23, 59, 59), False),  # Sunday
    ],
)
def test_is_end_of_period_week(dt, expected):
    assert is_end_of_period(dt, "week") == expected


@pytest.mark.parametrize(
    "dt,expected",
    [
        (datetime(2023, 7, 1, 0, 0, 0), True),
        (datetime(2023, 6, 30, 23, 59, 59), False),
    ],
)
def test_is_end_of_period_month(dt, expected):
    assert is_end_of_period(dt, "month") == expected


@pytest.mark.parametrize(
    "dt,expected",
    [
        (datetime(2024, 1, 1, 0, 0, 0), True),
        (datetime(2023, 12, 31, 23, 59, 59), False),
    ],
)
def test_is_end_of_period_year(dt, expected):
    assert is_end_of_period(dt, "year") == expected


@given(st.datetimes(min_value=datetime(1999, 1, 1), max_value=datetime(2023, 12, 31)))
def test_is_end_of_period_interval_property(dt):
    assert is_end_of_period(dt, "interval") == True  # noqa: E712


@given(st.datetimes(min_value=datetime(1999, 1, 1), max_value=datetime(2023, 12, 31)))
def test_is_end_of_period_day_property(dt):
    assert is_end_of_period(dt, "day") == (dt.hour == 0 and dt.minute == 0 and dt.second == 0)


@given(st.datetimes(min_value=datetime(1999, 1, 1), max_value=datetime(2023, 12, 31)))
def test_is_end_of_period_week_property(dt):
    assert is_end_of_period(dt, "week") == (dt.weekday() == 0 and dt.hour == 0 and dt.minute == 0 and dt.second == 0)


@given(st.datetimes(min_value=datetime(1999, 1, 1), max_value=datetime(2023, 12, 31)))
def test_is_end_of_period_month_property(dt):
    assert is_end_of_period(dt, "month") == (dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0)


@given(st.datetimes(min_value=datetime(1999, 1, 1), max_value=datetime(2023, 12, 31)))
def test_is_end_of_period_year_property(dt):
    assert is_end_of_period(dt, "year") == (dt.month == 1 and dt.day == 1 and dt.hour == 0 and dt.minute == 0 and dt.second == 0)


# Test get_period_start_end
def test_get_period_start_end_day():
    dt = datetime(2023, 6, 15, 12, 30)
    start, end = get_period_start_end(dt, "day")
    assert start == datetime(2023, 6, 14, 0, 0, 0)
    assert end == datetime(2023, 6, 15, 0, 0, 0)


def test_get_period_start_end_week():
    dt = datetime(2023, 6, 15, 12, 30)  # Thursday
    start, end = get_period_start_end(dt, "week")
    assert start == datetime(2023, 6, 5, 0, 0, 0)  # Previous Monday
    assert end == datetime(2023, 6, 12, 0, 0, 0)  # Monday of the current week


def test_get_period_start_end_month():
    dt = datetime(2023, 6, 15, 12, 30)
    start, end = get_period_start_end(dt, "month")
    assert start == datetime(2023, 5, 1, 0, 0, 0)
    assert end == datetime(2023, 6, 1, 0, 0, 0)


def test_get_period_start_end_year():
    dt = datetime(2023, 6, 15, 12, 30)
    start, end = get_period_start_end(dt, "year")
    assert start == datetime(2022, 1, 1, 0, 0, 0)
    assert end == datetime(2023, 1, 1, 0, 0, 0)


@given(st.datetimes(min_value=datetime(1999, 1, 1), max_value=datetime(2023, 12, 31)), st.sampled_from(BUCKET_SIZES))
def test_get_period_start_end_properties(dt, bucket_size):
    start, end = get_period_start_end(dt, bucket_size)

    assert start < end, "Start must be before end"
    assert start <= dt <= end, "Start must be before or equal to dt and end must be after or equal to dt"

    if bucket_size != "interval":
        assert start.hour == 0 and start.minute == 0 and start.second == 0 and start.microsecond == 0, "Start must be at midnight"
        assert end.hour == 0 and end.minute == 0 and end.second == 0 and end.microsecond == 0, "End must be at midnight"

    if bucket_size == "interval":
        assert end == start, "Start and end must be the same when bucket_size is 'interval'"
    elif bucket_size == "day":
        assert end - start == timedelta(days=1), "End must be 1 day after start when bucket_size is 'day'"
    elif bucket_size == "week":
        assert end - start == timedelta(days=7), "End must be 7 days after start when bucket_size is 'week'"
        assert start.weekday() == 0 and end.weekday() == 0, "Start and end must be on the same day of the week"
    elif bucket_size == "month":
        assert start.day == 1 and end.day == 1, "Start and end must be on the first day of the month"
        assert (
            (start.year, start.month) == (end.year, end.month - 1) if end.month > 1 else (end.year - 1, 12)
        ), "Start and end must be on the same month"
    elif bucket_size == "year":
        assert start.month == 1 and start.day == 1
        assert end.month == 1 and end.day == 1
        assert end.year == start.year + 1


@given(st.datetimes())
def test_get_period_start_end_day_property(dt):
    start, end = get_period_start_end(dt, "day")
    assert end.date() == dt.date()
    assert start.date() == dt.date() - timedelta(days=1)


@given(st.datetimes())
def test_get_period_start_end_week_property(dt):
    start, end = get_period_start_end(dt, "week")
    assert start.weekday() == 0
    assert end.weekday() == 0
    assert (end - start).days == 7
    assert end <= dt
    assert (dt - end).days < 7


@given(st.datetimes())
def test_get_period_start_end_month_property(dt):
    start, end = get_period_start_end(dt, "month")
    assert start.day == 1
    assert end.day == 1
    assert end <= dt
    assert (dt.year, dt.month) == (end.year, end.month)


@given(st.datetimes(min_value=datetime(1999, 1, 1), max_value=datetime(2023, 12, 31)))
def test_get_period_start_end_year_property(dt):
    start, end = get_period_start_end(dt, "year")
    assert start.month == 1 and start.day == 1
    assert end.month == 1 and end.day == 1
    assert end.year == start.year + 1
    assert start <= dt <= end
    assert dt.year == start.year


@pytest.mark.parametrize(
    "dt",
    [
        datetime(2023, 12, 31, 23, 59, 59, 999999),  # Last microsecond of the year
        datetime(2024, 1, 1, 0, 0, 0),  # First moment of the year
        datetime(2023, 2, 28, 23, 59, 59, 999999),  # Last microsecond of February in a non-leap year
        datetime(2024, 2, 29, 23, 59, 59, 999999),  # Last microsecond of February in a leap year
        datetime(2023, 12, 31, 0, 0, 0),  # Start of the last day of the year
        datetime(2023, 1, 1, 0, 0, 0),  # Start of the first day of the year
    ],
)
def test_get_period_start_end_edge_cases(dt: datetime):
    for bucket_size in BUCKET_SIZES:
        start, end = get_period_start_end(dt, bucket_size)
        assert start <= dt, f"Start must be less than or equal to end for {bucket_size}"
        if bucket_size != "interval":
            assert is_end_of_period(end, bucket_size)
            assert is_end_of_period(start, bucket_size)


# Test get_bucket_sql
@pytest.mark.parametrize(
    "bucket_size,expected",
    [
        ("interval", "trading_interval"),
        ("day", "date_trunc('day', trading_interval)"),
        ("week", "date_trunc('week', trading_interval)"),
        ("month", "date_trunc('month', trading_interval)"),
        ("year", "date_trunc('year', trading_interval)"),
    ],
)
def test_get_bucket_sql(bucket_size, expected):
    assert get_bucket_sql(bucket_size) == expected


@given(st.sampled_from(BUCKET_SIZES))
def test_get_bucket_sql_property(bucket_size):
    result = get_bucket_sql(bucket_size)
    if bucket_size == "interval":
        assert result == "trading_interval"
    else:
        assert result == f"date_trunc('{bucket_size}', trading_interval)"


# Hypothesis tests


# Edge case tests


# Invalid input tests
def test_invalid_bucket_size():
    with pytest.raises(ValueError):
        get_period_start_end(datetime.now(), "invalid_bucket")

    with pytest.raises(ValueError):
        is_end_of_period(datetime.now(), "invalid_bucket")

    with pytest.raises(ValueError):
        get_bucket_sql("invalid_bucket")
