import decimal
from math import floor, log, pow
from typing import List, Union

from opennem.settings import settings

__log10 = 2.302585092994046

DEFAULT_PRECISION = settings.precision_default

ctx = decimal.Context()
ctx.prec = 20


def float_to_str(f):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, "f")


def cast_number(number: any) -> float:
    """ Cast to a float """
    number_float = float(number)

    return number_float


def num_sigfigs(n, sig):
    """
    Adapted significant figure count

    """
    multi = pow(10, sig - floor(log(n) / __log10) - 1)
    return round(n * multi) / multi


def sigfig_compact(n: Union[float, int], precision: int = DEFAULT_PRECISION) -> Union[float, int]:
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


def human2bytes(s: str) -> int:
    """
    >>> human2bytes('1M')
    1048576
    >>> human2bytes('1G')
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


def float_to_str(f: float) -> str:
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, "f")


def cast_trailing_nulls(series: List) -> List:
    """
    Cast trailing None's in a list series to 0's
    """
    for i, x in reversed(list(enumerate(series))):
        if x is None:
            series[i] = 0
        else:
            return series

    return series
