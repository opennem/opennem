"""
OpenNEM Energy Tools

"""
from decimal import Decimal, getcontext
from operator import attrgetter
from sys import maxsize
from typing import List, Optional, Union

from opennem.schema.core import BaseConfig

MAX_INTERVALS = maxsize - 1

context = getcontext()
context.prec = 9


class Point(BaseConfig):
    x: Decimal
    y: Decimal


def trapozedoid(p1: Point, p2: Point) -> float:
    """Trapezoidal area between two points"""
    width = p2.y - p1.y
    area = p1.x * width + ((p2.x - p1.x) * width) / 2

    return float(area)


def zero_nulls(number: Union[int, float, None]) -> float:
    if not number:
        return 0.0

    return number


def energy_sum(series: List[Union[int, float, None]], bucket_size_minutes: int) -> float:
    """Calcualte the energy sum of a series for an interval"""

    number_intervals = len(series) - 1
    interval_size = bucket_size_minutes / len(series)

    if len(series) < 1:
        raise Exception("Requires at least one value in the series")

    if bucket_size_minutes <= 0 or bucket_size_minutes > maxsize:
        raise Exception("Invalid bucket size")

    if bucket_size_minutes % 1 != 0:
        raise Exception("Not a round interval size in minutes")

    if number_intervals < 1 or number_intervals >= MAX_INTERVALS:
        raise Exception("Invalid number of intervals")

    # 0 out all nulls
    series = [zero_nulls(n) for n in series]

    y_series = [i * interval_size for i in range(len(series))]

    # build point objects from y_series and zeroed x values
    series_points = [Point(x=series[i], y=y) for i, y in enumerate(y_series)]

    # sort by y value ascending 0 ... N
    series_points.sort(key=attrgetter("y"))

    area = 0.0
    p1 = None
    p2 = None

    for i in range(number_intervals):
        p1 = series_points[i]
        p2 = series_points[i + 1]

        area += trapozedoid(p1, p2)

    # convert back to hours
    area = area / 60

    return area
