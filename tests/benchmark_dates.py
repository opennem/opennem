from datetime import datetime

import pytest

from opennem.utils.dates import parse_date


@pytest.mark.benchmark(
    group="date_parser",
    min_rounds=50,
)
@pytest.mark.parametrize(
    "date_str,date_dt",
    [
        ("1/11/08 0:00", datetime(2008, 11, 1, 0, 0, 0)),
        ("1/9/19 4:00", datetime(2019, 9, 1, 4, 0, 0)),
        ("30/9/19 4:00", datetime(2019, 9, 30, 4, 0, 0)),
    ],
)
def test_benchmark_dateparser(benchmark, date_str, date_dt):
    date_subject_dt = benchmark(parse_date, date_str=date_str)
    assert date_subject_dt == date_dt


@pytest.mark.benchmark(
    group="date_parser",
    min_rounds=50,
)
@pytest.mark.parametrize(
    "date_str,date_dt",
    [
        ("1/11/08 0:00", datetime(2008, 11, 1, 0, 0, 0)),
        ("1/9/19 4:00", datetime(2019, 9, 1, 4, 0, 0)),
        ("30/9/19 4:00", datetime(2019, 9, 30, 4, 0, 0)),
    ],
)
def test_benchmark_dateparser_optimized(benchmark, date_str, date_dt):
    date_subject_dt = benchmark(parse_date, date_str=date_str, use_optimized=True)
    assert date_subject_dt == date_dt
