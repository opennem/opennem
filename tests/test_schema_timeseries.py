from datetime import date, datetime

import pytest

from opennem.api.time import human_to_interval, human_to_period
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkNEM


@pytest.mark.parametrize(
    ["ts", "start_expected", "end_expected", "interval_expected", "length_expected"],
    [
        # Test 1 hour inclusive
        (
            OpennemExportSeries(
                start=datetime.fromisoformat("2021-01-15 12:00:00+00:00"),
                end=datetime.fromisoformat("2021-01-15 13:00:00+00:00"),
                network=NetworkNEM,
                interval=NetworkNEM.get_interval(),
                period=human_to_period("1h"),
            ),
            # Also testing timezone shift from UTC to NEM time
            datetime.fromisoformat("2021-01-15 12:00:00+00:00"),
            datetime.fromisoformat("2021-01-15 13:00:00+00:00"),
            "5m",
            13,  # number of 5 minute intervals in an hour _inclusive_
        ),
        # Test 1 week inclusive
        (
            OpennemExportSeries(
                start=datetime.fromisoformat("1997-05-05 12:45:00+00:00"),
                end=datetime.fromisoformat("2021-01-15 12:45:00+00:00"),
                network=NetworkNEM,
                interval=NetworkNEM.get_interval(),
                period=human_to_period("7d"),
            ),
            # Also testing timezone shift from UTC to NEM time
            datetime.fromisoformat("2021-01-08T12:45:00+00:00"),
            datetime.fromisoformat("2021-01-15T12:45:00+00:00"),
            "5m",
            2017,  # number of 5 minute intervals in a year
        ),
        # Years
        # @TODO work out wtf .. must be a year thing
        # (
        #     TimeSeries(
        #         start=datetime.fromisoformat("1997-05-05 12:45:00+10:00"),
        #         end=datetime.fromisoformat("2021-01-15 12:45:00+10:00"),
        #         network=NetworkNEM,
        #         year=2021,
        #         interval=human_to_interval("1d"),
        #         period=human_to_period("1Y"),
        #     ),
        #     # Expected
        #     datetime.fromisoformat("2021-01-01 00:00:00+10:00"),
        #     datetime.fromisoformat("2021-01-14 23:59:59+10:00"),
        #     "1d",
        #     15,
        # ),
        (
            OpennemExportSeries(
                start=datetime.fromisoformat("1997-05-05 12:45:00+00:00"),
                end=datetime.fromisoformat("2021-02-15 12:45:00+00:00"),
                network=NetworkNEM,
                year=2019,
                interval=human_to_interval("1d"),
                period=human_to_period("1Y"),
            ),
            # Expected
            datetime.fromisoformat("2019-01-01 00:00:00+10:00"),
            datetime.fromisoformat("2019-12-31 23:59:59+10:00"),
            "1d",
            365,
        ),
        (
            OpennemExportSeries(
                start=datetime.fromisoformat("1997-05-05 12:45:00+00:00"),
                end=datetime.fromisoformat("2021-02-15 12:45:00+00:00"),
                network=NetworkNEM,
                year=2020,
                interval=human_to_interval("1d"),
                period=human_to_period("1Y"),
            ),
            # Expected
            datetime.fromisoformat("2020-01-01 00:00:00+10:00"),
            datetime.fromisoformat("2020-12-31 23:59:59+10:00"),
            "1d",
            366,  # leap year
        ),
        # All
        (
            OpennemExportSeries(
                start=datetime.fromisoformat("1997-05-05 12:45:00+00:00"),
                end=datetime.fromisoformat("2020-02-15 12:45:00+00:00"),
                network=NetworkNEM,
                interval=human_to_interval("1M"),
                period=human_to_period("all"),
            ),
            # Expected results
            datetime.fromisoformat("1997-05-01 00:00:00+10:00"),
            datetime.fromisoformat("2020-01-31 23:59:59+10:00"),
            "1M",
            274,
        ),
        # Forecasts
        (
            OpennemExportSeries(
                start=datetime.fromisoformat("1997-05-05 12:45:00+00:00"),
                end=datetime.fromisoformat("2021-01-15 12:45:00+00:00"),
                network=NetworkNEM,
                interval=NetworkNEM.get_interval(),
                period=human_to_period("7d"),
                forecast=True,
            ),
            # Also testing timezone shift from UTC to NEM time
            datetime.fromisoformat("2021-01-15 12:45:00+00:00"),
            datetime.fromisoformat("2021-01-22 12:45:00+00:00"),
            "5m",
            2017,  # number of 5 minute intervals in a week
        ),
    ],
)
def test_schema_timeseries(
    ts: OpennemExportSeries,
    start_expected: datetime | date,
    end_expected: datetime | date,
    interval_expected: str,
    length_expected: int,
) -> None:
    subject_daterange = ts.get_range()

    assert str(subject_daterange.start) == str(start_expected), "Start string matches"
    assert subject_daterange.start == start_expected, "Start matches"
    assert str(subject_daterange.end) == str(end_expected), "End string matches"
    assert subject_daterange.end == end_expected, "End matches"
    assert subject_daterange.trunc == interval_expected, "Interval matches"
    # assert subject_daterange.length == length_expected, "Correct length"
