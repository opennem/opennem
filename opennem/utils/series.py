"""
Utilities to work on series

"""

from operator import add
from typing import List


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
                if s2d[k] != 0:
                    d[k] = (s2d[k] - s1d[k]) / s2d[k] * 100
                elif s1d[k] == 0:
                    d[k] = 0.0
            elif isinstance(s1d[k], float):
                d[k] = -100
            elif isinstance(s2d[k], float):
                d[k] = 100

    return list(d.keys()), list(d.values())
