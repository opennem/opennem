"""
Timezone-related classes and functions.

Some methods adapted from the Django project
"""
from datetime import datetime, timedelta
from datetime import timezone as pytimezone


def get_fixed_timezone(offset: timedelta | int) -> pytimezone:
    """Return a tzinfo instance with a fixed offset from UTC."""

    if isinstance(offset, timedelta):
        offset = offset.total_seconds() // 60

    sign = "-" if offset < 0 else "+"
    hhmm = "%02d%02d" % divmod(abs(offset), 60)
    name = sign + hhmm

    return pytimezone(timedelta(minutes=offset), name)


def is_aware(value: datetime) -> bool:
    """
    Determines if a given datetime.datetime is aware.

    The concept is defined in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """

    return value.utcoffset() is not None


def is_naive(value: datetime) -> bool:
    """
    Determines if a given datetime.datetime is naive.

    The concept is defined in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """

    return value.utcoffset() is None


def make_aware(value: datetime, timezone: pytimezone = None) -> datetime:
    """Make a naive datetime.datetime in a given time zone aware."""

    if timezone is None:
        timezone = pytimezone.utc

    # Check that we won't overwrite the timezone of an aware datetime.
    if is_aware(value):
        raise ValueError("make_aware expects a naive datetime, got %s" % value)

    # This may be wrong around DST changes!
    return value.replace(tzinfo=timezone)


def make_naive(value: datetime, timezone: pytimezone = None) -> datetime:
    """Make an aware datetime.datetime naive in a given time zone."""

    if timezone is None:
        timezone = pytimezone.utc

    # Emulate the behavior of astimezone() on Python < 3.6.
    if is_naive(value):
        raise ValueError("make_naive() cannot be applied to a naive datetime")

    return value.astimezone(timezone).replace(tzinfo=None)
