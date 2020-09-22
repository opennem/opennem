import re
from datetime import timedelta

UNITS = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}


def human_to_interval(s: str) -> timedelta:
    return timedelta(
        **{
            UNITS.get(m.group("unit").lower(), "seconds"): int(m.group("val"))
            for m in re.finditer(
                r"(?P<val>\d+)(?P<unit>[smhdw]?)", s, flags=re.I
            )
        }
    )
