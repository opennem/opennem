import decimal
import logging
import random
import re
from datetime import datetime
from math import floor, log, pow  # noqa: no-name-module
from re import Match
from typing import Any

from opennem import settings

logger = logging.getLogger("opennem.utils.numbers")

__log10 = 2.302585092994046

DEFAULT_PRECISION = settings.precision_default

ctx = decimal.Context()
ctx.prec = 20


def generate_random_number_series(length: int, max_value: float = 100.00) -> list[float]:
    """ """
    return [round(random.uniform(0, max_value), 2) for _ in range(length)]


def float_to_str(f: float) -> str:
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, "f")


def cast_number(number: Any) -> float:
    """Cast to a float"""
    number_float = float(number)

    return number_float


def num_sigfigs(n: float, sig: int) -> float:
    """
    Adapted significant figure count

    """
    multi = pow(10, sig - floor(log(n) / __log10) - 1)
    return round(n * multi) / multi


def sigfig_compact(n: float | int, precision: int = DEFAULT_PRECISION) -> float | int:
    """
    Compact significant figure formatting
    """

    if not isinstance(n, float):
        n = cast_number(n)

    n_abs = abs(n)
    is_neg = n < 0

    if n == 0:
        return 0

    if n_abs >= pow(10, precision):
        n = floor(n_abs)
    else:
        n = num_sigfigs(n_abs, precision)

    if is_neg:
        n *= -1

    if n == int(n):
        return int(n)

    return n


def human2bytes(s: str) -> int | None:
    """
    >>> human2bytes("1M")
    1048576
    >>> human2bytes("1G")
    1073741824
    """
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        pass

    symbols = "BKMGTPEZY"
    letter = s[-1:].strip().upper()
    num = float(s[:-1])
    prefix = {symbols[0]: 1}

    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10

    return int(num * prefix[letter])


def cast_trailing_nulls(series: list) -> list:
    """
    Cast trailing None's in a list series to 0's
    """
    for i, x in reversed(list(enumerate(series))):
        if x is None:
            series[i] = 0
        else:
            return series

    return series


def trim_nulls(series: dict) -> dict:
    """
    Trime preceding and trailing nulls in dict
    """
    in_values = False
    _remove_keys = []

    for i, x in series.items():
        if x is not None:
            in_values = True

        if in_values:
            continue

        _remove_keys.append(i)

    for dt in reversed(series.keys()):
        v = series[dt]

        if v is not None:
            break

        _remove_keys.append(dt)

    for k in _remove_keys:
        series.pop(k, None)

    return series


def pad_time_series(series: dict, start_date: datetime, end_date: datetime, pad_with: int | None = 0) -> dict:
    """Pad out time series to start and end date"""

    series_dates = series.keys()
    series_min_date = min(series_dates)
    series_max_date = max(series_dates)

    to_pad = 0

    if start_date < series_min_date:
        # @TODO date - date / interval
        logger.warning("Start date padding out")
        to_pad += 1

    if end_date > series_max_date:
        logger.warning("End date pad out")
        to_pad += 1

    return series


__re_filesize_from_string = re.compile(r"^(\d+\.?\d+?).*?(KB|MB)$")


def filesize_from_string(subject: str) -> tuple[float | None, str | None]:
    """Extract a file size from a string.

    Returns size and units

    ex. "203 KB" -> 203, KB
    """
    m = re.match(__re_filesize_from_string, subject)

    if not m:
        return None, None

    size: float | None = None
    units: str | None = None

    try:
        size = float(m.group(1))
        units = m.group(2)
    except IndexError:
        pass

    return size, units


def compact_json_output_number_series(json_envelope: str) -> str:
    """Will take a JSON envelope, find data keys with numerical series and compact them without newline characters

    @NOTE only applies with json output set with indent parameter

    Args:
        json_str str: a JSON envelope in string form

    Returns:
        str: the entire compacted output JSON envelope
    """

    re_compact_json_number_output = r"history\"\:.*\"data\":\ ?\[(?P<number_series>[\ \,\d+^\]]+)"

    # catch cases of dicts or objects being passed
    if not isinstance(json_envelope, str):
        return json_envelope

    # Groups to replace and their replacements
    replace_groups = {
        "\n": "",
        " ": "",
        ",": ", ",
        ".0": "",
    }

    def number_series_normalizer(match: Match) -> str:
        if not isinstance(match, Match):
            logger.error(f"Invalid match object in compact_json_output_number_series: {match}")

        if not match:
            logger.error("No data series match in output")

        try:
            number_series = match.group("number_series")
        except IndexError:
            logger.error("No number series group in match")
            return ""

        logger.debug(number_series)

        compacted_number_series: str = number_series.strip()

        # Replace newline and possible spaces
        for k, v in replace_groups.items():
            compacted_number_series = compacted_number_series.replace(k, v)

        return f"data: [{compacted_number_series}]"

    compacted_output = re.sub(re_compact_json_number_output, number_series_normalizer, json_envelope, flags=re.DOTALL)

    return compacted_output


# debug entry point
if __name__ == "__main__":
    """unit test base for compact_json_output_number_series"""
    from opennem.utils.project_path import get_project_path

    test_path = get_project_path() / "data" / "nsw_7d.json"

    with open(test_path) as fh:
        json_str = fh.read()

    compacted_json = compact_json_output_number_series(json_str)

    print(compacted_json)
