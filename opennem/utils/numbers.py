import decimal
from math import floor, log, pow
from typing import Union

import numpy as np

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


def sigfig_compact(
    n: Union[float, int], precision: int = DEFAULT_PRECISION
) -> float:
    """
        Compact significant figure formatting
    """

    if not isinstance(n, float):
        n = cast_number(n)

    n_abs = abs(n)
    is_neg = n < 0

    if n == 0:
        return n

    if n_abs >= pow(10, precision):
        n = floor(n_abs)
    else:
        n = num_sigfigs(n_abs, precision)

    if is_neg:
        n *= -1

    return n

