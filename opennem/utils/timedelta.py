""" OpenNEM Timedelta utilities """
from datetime import timedelta


def timedelta_to_string(td_object: timedelta) -> str:
    """Converts a timedelta to H:m:s format"""
    seconds = int(td_object.total_seconds())
    periods = [("Y", 60 * 60 * 24 * 365), ("M", 60 * 60 * 24 * 30), ("d", 60 * 60 * 24), ("h", 60 * 60), ("m", 60), ("s", 1)]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            strings.append(f"{period_value}{period_name}")

    return ":".join(strings)
