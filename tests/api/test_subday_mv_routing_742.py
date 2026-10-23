"""Routing predicate for serving sub-daily data queries from fueltech_intervals_mv (#742)."""

from datetime import UTC, datetime, timedelta

import pytest

from opennem.api.data.schema import DataMetric
from opennem.api.queries import SUBDAY_MV_TABLE, QueryType, get_timeseries_query, subday_mv_supported
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkNEM

END = datetime.now(UTC).replace(tzinfo=None)
START = END - timedelta(days=7)
SG = SecondaryGrouping


@pytest.mark.parametrize("interval", [Interval.INTERVAL, Interval.HALF_HOUR, Interval.HOUR])
@pytest.mark.parametrize("secondary", [None, [SG.FUELTECH], [SG.FUELTECH_GROUP]])
def test_routes_eligible_shapes(interval, secondary):
    assert subday_mv_supported(QueryType.DATA, interval, [DataMetric.POWER, Metric.EMISSIONS], secondary)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"query_type": QueryType.MARKET},
        {"query_type": QueryType.FACILITY},
        {"interval": Interval.DAY},
        {"interval": Interval.MONTH},
        {"metrics": [DataMetric.STORAGE_BATTERY]},
        {"metrics": [DataMetric.POWER, DataMetric.STORAGE_BATTERY]},
        {"metrics": []},
        {"secondary_groupings": [SG.RENEWABLE]},
        {"secondary_groupings": [SG.STATUS]},
        {"secondary_groupings": [SG.FUELTECH, SG.RENEWABLE]},
        {"facility_code": ["BAYSW"]},
        {"unit_code": ["BAYSW1"]},
    ],
)
def test_falls_back_for_ineligible_shapes(kwargs):
    base = {
        "query_type": QueryType.DATA,
        "interval": Interval.INTERVAL,
        "metrics": [DataMetric.POWER],
        "secondary_groupings": [SG.FUELTECH],
    }
    assert not subday_mv_supported(**{**base, **kwargs})


def _sql(use_subday_mv, **kwargs):
    kw = {
        "query_type": QueryType.DATA,
        "network": NetworkNEM,
        "metrics": [DataMetric.POWER],
        "interval": Interval.INTERVAL,
        "date_start": START,
        "date_end": END,
        "primary_grouping": PrimaryGrouping.NETWORK_REGION,
        "secondary_groupings": [SG.FUELTECH],
    }
    return get_timeseries_query(**{**kw, **kwargs}, use_subday_mv=use_subday_mv)[0]


def test_query_reads_view_when_routed():
    sql = _sql(True)
    assert f"FROM {SUBDAY_MV_TABLE} FINAL" in sql
    assert "unit_intervals" not in sql


def test_flag_off_reads_raw():
    sql = _sql(False)
    assert "FROM unit_intervals FINAL" in sql
    assert SUBDAY_MV_TABLE not in sql


def test_setting_default_drives_routing(monkeypatch):
    from opennem import settings

    monkeypatch.setattr(settings, "clickhouse_subday_mv_routing", False)
    assert "FROM unit_intervals FINAL" in _sql(None)
    monkeypatch.setattr(settings, "clickhouse_subday_mv_routing", True)
    assert f"FROM {SUBDAY_MV_TABLE} FINAL" in _sql(None)


def test_ineligible_shape_stays_raw_even_when_on():
    assert "FROM unit_intervals FINAL" in _sql(True, secondary_groupings=[SG.RENEWABLE])
    assert "FROM unit_intervals FINAL" in _sql(True, metrics=[DataMetric.STORAGE_BATTERY])
    assert "FROM unit_intervals FINAL" in _sql(True, interval=Interval.INTERVAL, facility_code=["X"])


def test_daily_interval_unchanged():
    sql = _sql(True, interval=Interval.DAY, date_start=datetime(2026, 1, 1), date_end=datetime(2026, 3, 1))
    assert SUBDAY_MV_TABLE not in sql
    assert "fueltech_intervals_daily_mv" in sql


def test_old_windows_stay_raw():
    old = END - timedelta(days=400)
    assert not subday_mv_supported(QueryType.DATA, Interval.INTERVAL, [DataMetric.POWER], None, date_start=old)
    assert subday_mv_supported(QueryType.DATA, Interval.INTERVAL, [DataMetric.POWER], None, date_start=START)
    assert "FROM unit_intervals FINAL" in _sql(True, date_start=old, date_end=old + timedelta(days=7))


def test_age_guard_boundary(monkeypatch):
    from opennem import settings

    monkeypatch.setattr(settings, "clickhouse_subday_mv_max_age_days", 10)
    now = datetime(2026, 10, 24, 12)
    kw = {"now": now, "metrics": [DataMetric.POWER], "secondary_groupings": None}
    assert subday_mv_supported(QueryType.DATA, Interval.HOUR, date_start=now - timedelta(days=10), **kw)
    assert not subday_mv_supported(QueryType.DATA, Interval.HOUR, date_start=now - timedelta(days=11), **kw)
