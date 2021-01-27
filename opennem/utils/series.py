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
    for k, v in s1d.items():
        if k in s2d:
            d[k] = s2d[k] - s1d[k]
    return list(d.keys()), list(d.values())
