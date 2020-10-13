import re
from datetime import datetime, timedelta
from typing import List

from pytz import timezone

UNITS = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}


def human_to_timedelta(s: str) -> timedelta:
    return timedelta(
        **{
            UNITS.get(m.group("unit").lower(), "seconds"): int(m.group("val"))
            for m in re.finditer(
                r"(?P<val>\d+)(?P<unit>[smhdw]?)", s, flags=re.I
            )
        }
    )


def dt_floor(dt: datetime, interval=5) -> datetime:
    """
        Round a datetime down to the nearest interval in minutes

    """
    return dt - timedelta(
        minutes=dt.minute % interval,
        seconds=dt.second,
        microseconds=dt.microsecond,
    )


def dt_series(tz: timezone = timezone("UTC")) -> List[datetime]:
    """
        Generate a datetime series

    """
    end = dt_floor(tz.localize(datetime.now()))

    start = end - timedelta(days=7)
    interval = timedelta(minutes=5)

    dc_current = start
    series = []

    while dc_current <= end:
        series.append(dc_current)
        dc_current += interval

    return series
