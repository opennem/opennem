"""
Utilities to work on series

"""

from datetime import datetime
from math import isclose
from operator import add
from typing import Dict, List, Tuple


def add_series(*args) -> List:
    return list(map(add, *args))


def series_diff(s1, s2):
    s2d = {i[0]: i[1] for i in s2}
    s1d = {i[0]: i[1] for i in s1}
    d = dict()
    for k in s1d.keys():
        if k in s2d:
            if isinstance(s2d[k], float) and isinstance(s1d[k], float):
                d[k] = s2d[k] - s1d[k]
            elif isinstance(s1d[k], float):
                d[k] = -1 * s1d[k]
            elif isinstance(s2d[k], float):
                d[k] = s2d[k]

    return list(d.keys()), list(d.values())


def series_diff_percentage(s1, s2):
    s2d = {i[0]: i[1] for i in s2}
    s1d = {i[0]: i[1] for i in s1}
    d = dict()
    for k in s1d.keys():
        if k in s2d:
            if isinstance(s2d[k], float) and isinstance(s1d[k], float):
                if s2d[k] == s1d[k]:
                    d[k] = 0

                if s1d[k] == 0 and s2d[k] > 0:
                    d[k] = 100

                if s1d[k] != 0:
                    try:
                        d[k] = (abs(s1d[k]) - abs(s2d[k])) / abs(s1d[k]) * 100 * -1
                    except ZeroDivisionError:
                        pass

            elif isinstance(s1d[k], float):
                d[k] = 100
            elif isinstance(s2d[k], float):
                d[k] = 100

    return list(d.keys()), list(d.values())


def are_approx_equal(actual: float, desired: float) -> bool:
    if actual == desired:
        return True

    if not desired or not actual:
        return True

    return isclose(actual, desired, abs_tol=0.5, rel_tol=0.0001)


def series_are_equal(
    s1: List[Tuple[datetime, float]],
    s2: List[Tuple[datetime, float]],
) -> Dict:
    s2d = {i[0]: i[1] for i in s2}
    s1d = {i[0]: i[1] for i in s1}
    d = dict()

    for k in s1d.keys():
        if k in s2d:
            d[k] = are_approx_equal(s1d[k], s2d[k])

    return d


def series_not_close(
    s1: List[Tuple[datetime, float]],
    s2: List[Tuple[datetime, float]],
) -> Dict:
    s2d = {i[0]: i[1] for i in s2}
    s1d = {i[0]: i[1] for i in s1}
    d = dict()

    for k in s1d.keys():
        if k in s2d:
            if not are_approx_equal(s1d[k], s2d[k]):
                if s2d[k] and s1d[k]:
                    d[k.isoformat()] = {"v2": s1d[k], "v3": s2d[k]}

    return d


def series_trim_to_date(
    s1: List[Tuple[datetime, float]],
    s2: List[Tuple[datetime, float]],
) -> Tuple[List, List]:
    s2d = {i[0]: i[1] for i in s2}
    s1d = {i[0]: i[1] for i in s1}
    d1 = []
    d2 = []

    for k in s1d.keys():
        if k in s2d:
            if s1d[k] and s2d[k]:
                d1.append(s1d[k])
                d2.append(s2d[k])

    return d1, d2
