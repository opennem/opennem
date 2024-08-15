from datetime import datetime

import pytest

from opennem.recordreactor.buckets import map_date_start_to_season


# Unit tests
@pytest.mark.parametrize(
    "date, expected_season",
    [
        (datetime(2023, 12, 1), "summer"),
        (datetime(2023, 3, 1), "autumn"),
        (datetime(2023, 6, 1), "winter"),
        (datetime(2023, 9, 1), "spring"),
        (datetime(2023, 1, 1), "summer"),
        (datetime(2023, 4, 30), "autumn"),
        (datetime(2023, 7, 31), "winter"),
        (datetime(2023, 10, 31), "spring"),
    ],
)
def test_map_date_start_to_season_specific_dates(date, expected_season):
    assert map_date_start_to_season(date) == expected_season


def test_map_date_start_to_season_leap_year():
    assert map_date_start_to_season(datetime(2024, 2, 29)) == "summer"


def test_map_date_start_to_season_error():
    with pytest.raises(ValueError):
        map_date_start_to_season(datetime(2023, 13, 1))  # Invalid month
