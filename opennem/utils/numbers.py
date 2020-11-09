from math import floor, log10, pow
from typing import Union

from opennem.settings import settings

DEFAULT_PRECISION = settings.precision_default


def cast_number(number: any) -> float:
    """ Cast to a float """
    number_float = float(number)

    return number_float


def _precision(value: float, precision: int) -> Union[float, int]:
    """ """
    if value == 0:
        return 0

    _prec = value

    try:
        _prec = round(value, -int(floor(log10(value))) + (precision - 1))
    except ValueError:
        pass

    return _prec


def _count_sigfigs(number) -> int:
    """Returns the number of significant digits in a number"""
    number = repr(float(number))

    tokens = number.split(".")
    whole_num = tokens[0].lstrip("0")

    if len(tokens) > 2:
        raise ValueError(
            'Invalid number "%s" only 1 decimal allowed' % (number)
        )

    if len(tokens) == 2:
        decimal_num = tokens[1].rstrip("0")
        return len(whole_num) + len(decimal_num)

    return len(whole_num)


def to_precision(
    value: float, precision: int = DEFAULT_PRECISION,
) -> Union[float, int]:
    """
        Preserve integer all significance and apply remaining precision required to
        fractional part
    """
    value = cast_number(value)
    value_int = int(value)

    value_int_significance = _count_sigfigs(value_int)
    value_fractional = value - value_int

    if value == value_int:
        return value_int

    if value_int > pow(10, precision - 1):
        return value_int

    if value_int_significance >= precision:
        return value_int

    remaining_precision = precision - value_int_significance

    remaining_precision_min = round(
        pow(0.1, remaining_precision), remaining_precision
    )

    if value_fractional < remaining_precision_min:
        return value_int + round(value_fractional, remaining_precision)

    value_fractional = _precision(
        value_fractional, precision - value_int_significance
    )

    result = value_int + value_fractional

    return result

