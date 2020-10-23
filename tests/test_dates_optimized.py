from datetime import datetime

import pytest

from opennem.utils.dates import optimized_data_parser


@pytest.mark.parametrize(
    "date_str,date_dt",
    [
        ("1/11/08 0:00", datetime(2008, 11, 1, 0, 0, 0)),
        ("1/9/19 4:00", datetime(2019, 9, 1, 4, 0, 0)),
        ("30/9/19 4:00", datetime(2019, 9, 30, 4, 0, 0)),
        ("2020/06/01 21:35:00", datetime(2020, 6, 1, 21, 35, 0)),
        ("2020/10/07 10:15:00", datetime(2020, 10, 7, 10, 15, 0)),
        ("27/9/2019  2:55:00 pm", datetime(2019, 9, 27, 14, 55, 0)),
        ("20201008133000", datetime(2020, 10, 8, 13, 30, 0, 0)),
    ],
)
def test_dateparser_optimized(benchmark, date_str, date_dt):
    date_subject_dt = optimized_data_parser(date_str)
    assert date_subject_dt == date_dt
