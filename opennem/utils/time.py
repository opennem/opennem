import re
from datetime import datetime, timedelta

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
            for m in re.finditer(r"(?P<val>\d+)(?P<unit>[smhdw]?)", s, flags=re.IGNORECASE)
        }
    )


def dt_floor(dt: datetime, interval: int = 5) -> datetime:
    """
    Round a datetime down to the nearest interval in minutes

    """
    return dt - timedelta(
        minutes=dt.minute % interval,
        seconds=dt.second,
        microseconds=dt.microsecond,
    )
