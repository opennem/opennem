"""
Timezone-related classes and functions.

Some methods adapted from the Django project
"""

from datetime import UTC, datetime, timedelta
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


def make_aware(value: datetime, timezone: pytimezone | None = None) -> datetime:
    """Make a naive datetime.datetime in a given time zone aware."""

    if timezone is None:
        timezone = UTC

    # Check that we won't overwrite the timezone of an aware datetime.
    if is_aware(value):
        raise ValueError(f"make_aware expects a naive datetime, got {value}")

    # This may be wrong around DST changes!
    return value.replace(tzinfo=timezone)


def make_naive(value: datetime, timezone: pytimezone | None = None) -> datetime:
    """Make an aware datetime.datetime naive in a given time zone."""

    if timezone is None:
        timezone = UTC

    # Emulate the behavior of astimezone() on Python < 3.6.
    if is_naive(value):
        raise ValueError("make_naive() cannot be applied to a naive datetime")

    return value.astimezone(timezone).replace(tzinfo=None)


def strip_timezone(value: datetime) -> datetime:
    """Strip the timezone from a datetime.datetime."""
    if is_naive(value):
        raise ValueError("strip_timezone() cannot be applied to a naive datetime")

    return value.replace(tzinfo=None)


def get_timezone_for_state(state: str) -> str:
    """Returns the timezone for a given state"""

    match state.upper():
        case "QLD":
            return "Australia/Brisbane"
        case "NSW":
            return "Australia/Sydney"
        case "VIC":
            return "Australia/Melbourne"
        case "TAS":
            return "Australia/Hobart"
        case "SA":
            return "Australia/Adelaide"
        case "NT":
            return "Australia/Darwin"
        case "WA":
            return "Australia/Perth"
        case _:
            raise ValueError(f"Invalid state provided: {state}")
