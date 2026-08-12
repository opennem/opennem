"""Interior gap filling in the timeseries formatter (#615).

A bucket a series is missing *inside* its own lifetime means "no data", which is a
different fact from an explicit 0. These assert the point is emitted as null, and that
nothing is invented outside a series' first and last reading.
"""

from datetime import date, datetime

from opennem.api.timeseries import format_timeseries_response
from opennem.core.grouping import PrimaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval


def _format(results, interval):
    return format_timeseries_response(
        network="NEM",
        metrics=[Metric.ENERGY],
        interval=interval,
        primary_grouping=PrimaryGrouping.NETWORK,
        secondary_groupings=None,
        results=results,
        facility_code=["ERARING"],
    )


def _series(response, name):
    return next(r["data"] for r in response[0]["results"] if r["name"] == name)


def test_missing_interior_day_returns_explicit_null():
    """ER04 has no row for 2000-02-20 while its siblings do — the repro from #615."""
    results = []
    for unit, days in {"ER01": [18, 19, 20, 21, 22], "ER04": [18, 19, 21, 22]}.items():
        results += [{"interval": date(2000, 2, d), "unit_code": unit, "energy": 100.0} for d in days]

    data = _series(_format(results, Interval.DAY), "energy_ER04")

    assert [v for _, v in data] == [100.0, 100.0, None, 100.0, 100.0]
    assert data[2][0].startswith("2000-02-20")


def test_edges_are_not_extended():
    """A unit that starts late or retires early keeps its own bounds — no fabricated rows."""
    results = [{"interval": date(2000, 2, d), "unit_code": "ER01", "energy": 1.0} for d in (18, 19, 20, 21, 22)]
    results += [{"interval": date(2000, 2, d), "unit_code": "ER04", "energy": 1.0} for d in (19, 21)]

    data = _series(_format(results, Interval.DAY), "energy_ER04")

    assert [(ts[:10], v) for ts, v in data] == [
        ("2000-02-19", 1.0),
        ("2000-02-20", None),
        ("2000-02-21", 1.0),
    ]


def test_five_minute_interior_gap_filled():
    results = [{"interval": datetime(2000, 2, 20, 0, m), "unit_code": "ER01", "energy": 1.0} for m in (0, 5, 10, 15, 20)]
    results += [{"interval": datetime(2000, 2, 20, 0, m), "unit_code": "ER04", "energy": 1.0} for m in (0, 20)]

    data = _series(_format(results, Interval.INTERVAL), "energy_ER04")

    assert [v for _, v in data] == [1.0, None, None, None, 1.0]


def test_calendar_interval_fills_against_observed_buckets():
    """1M has no constant width, so the fill uses buckets present elsewhere in the response."""
    results = [{"interval": datetime(2000, m, 1), "unit_code": "ER01", "energy": 1.0} for m in (1, 2, 3, 4)]
    results += [{"interval": datetime(2000, m, 1), "unit_code": "ER04", "energy": 1.0} for m in (1, 3)]

    data = _series(_format(results, Interval.MONTH), "energy_ER04")

    assert [(ts[:7], v) for ts, v in data] == [("2000-01", 1.0), ("2000-02", None), ("2000-03", 1.0)]


def test_complete_series_is_untouched():
    results = [{"interval": date(2000, 2, d), "unit_code": "ER01", "energy": 1.0} for d in (18, 19, 20)]

    data = _series(_format(results, Interval.DAY), "energy_ER01")

    assert [v for _, v in data] == [1.0, 1.0, 1.0]
