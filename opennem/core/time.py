from typing import List

from opennem.core.loader import load_data
from opennem.schema.time import TimeInterval, TimePeriod

SUPPORTED_PERIODS = ["7D", "1M", "1Y", "ALL"]

SUPPORTED_INTERVALS = ["5M", "15M", "30M", "1D", "1H", "1M"]


def load_intervals() -> List[TimeInterval]:
    interval_dicts = load_data("intervals.json")

    intervals = [TimeInterval(**i) for i in interval_dicts]

    return intervals


INTERVALS = load_intervals()

PERIODS = []


def get_interval(interval_human: str) -> TimeInterval:
    interval_lookup = list(
        filter(lambda x: x.interval_human == interval_human, INTERVALS)
    )

    if interval_lookup:
        return interval_lookup.pop()

    raise Exception("Invalid interval {} not mapped".format(interval_human))

