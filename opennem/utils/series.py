"""
Utilities to work on series

"""

from operator import add
from typing import List


def add_series(*args) -> List:
    return list(map(add, *args))
