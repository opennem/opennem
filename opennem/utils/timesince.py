import calendar
from datetime import UTC, datetime, timedelta

from opennem.utils.timezone import is_aware

TIME_STRINGS = {
    "year": ("%(num)d year", "%(num)d years"),
    "month": ("%(num)d month", "%(num)d months"),
    "week": ("%(num)d week", "%(num)d weeks"),
    "day": ("%(num)d day", "%(num)d days"),
    "hour": ("%(num)d hour", "%(num)d hours"),
    "minute": ("%(num)d minute", "%(num)d minutes"),
}

TIMESINCE_CHUNKS = (
    (60 * 60 * 24 * 365, "year"),
    (60 * 60 * 24 * 30, "month"),
    (60 * 60 * 24 * 7, "week"),
    (60 * 60 * 24, "day"),
    (60 * 60, "hour"),
    (60, "minute"),
)


def timesince(
    d: datetime | None = None,
    now: datetime | None = None,
    reversed: bool = False,
    depth: int = 2,
    none_value: str = "Never",
) -> str:
    """
    Take two datetime objects and return the time between d and now as a nicely
    formatted string, e.g. "10 minutes". If d occurs after now, return
    "0 minutes".

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored. Up to `depth` adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    `time_strings` is an optional dict of strings to replace the default
    TIME_STRINGS dict.

    `depth` is an optional integer to control the number of adjacent time
    units returned.

    Adapted from
    https://web.archive.org/web/20060617175230/http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    time_strings = TIME_STRINGS

    if not d:
        return none_value

    if depth <= 0:
        raise ValueError("depth must be greater than 0.")

    # Convert date to datetime for comparison.
    if not isinstance(d, datetime):
        d = datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime):
        now = datetime(now.year, now.month, now.day)

    now = now or datetime.now(UTC if is_aware(d) else None)

    if reversed:
        d, now = now, d
    delta = now - d

    # Deal with leapyears by subtracing the number of leapdays
    leapdays = calendar.leapdays(d.year, now.year)
    if leapdays != 0:
        if calendar.isleap(d.year):
            leapdays -= 1
        elif calendar.isleap(now.year):
            leapdays += 1
    delta -= timedelta(leapdays)

    # ignore microseconds
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return time_strings["minute"][0] % {"num": 0}
    for i, (seconds, _name) in enumerate(TIMESINCE_CHUNKS):  # noqa: B007
        count = since // seconds
        if count != 0:
            break
    else:
        return time_strings["minute"][0] % {"num": 0}
    result = []
    current_depth = 0
    while i < len(TIMESINCE_CHUNKS) and current_depth < depth:
        seconds, name = TIMESINCE_CHUNKS[i]
        count = since // seconds
        if count == 0:
            break
        if count == 1:
            time_string = time_strings[name][0] % {"num": count}
        else:
            time_string = time_strings[name][1] % {"num": count}
        result.append(time_string)
        since -= seconds * count
        current_depth += 1
        i += 1
    return ", ".join(result)


def timeuntil(d: datetime, now: datetime | None = None, depth: int = 2) -> str:
    """
    Like timesince, but return a string measuring the time until the given time.
    """
    return timesince(d, now, reversed=True, depth=depth)
