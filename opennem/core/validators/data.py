""""
OpenNEM Data Validators

"""
from datetime import datetime, timedelta
from decimal import Decimal

from datedelta import datedelta

from opennem.utils.dates import num_intervals_between_datetimes

ValidNumber = float | int | None | Decimal


def validate_data_outputs(
    series: list[ValidNumber],
    interval_size: timedelta | datedelta,
    start_date: datetime,
    end_date: datetime,
) -> bool:
    """
    Checks that the series has the correct length considering start and end date and the series edge type
    """
    number_of_intervals = num_intervals_between_datetimes(interval_size, start_date, end_date)

    if len(series) != number_of_intervals:
        raise Exception(f"validate_data_outputs: Got {len(series)} intervals, expected {number_of_intervals}")

    return True
