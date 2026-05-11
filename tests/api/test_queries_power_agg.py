"""Lock the per-interval aggregation for DataMetric.POWER.

POWER (MW) is an instantaneous rate, so 5m -> 1h must average, and 5m/daily-MV ->
1d+ must compute an interval-weighted average. ENERGY/EMISSIONS/MARKET_VALUE
remain summed because they are per-interval cumulative quantities.

Regression test for opennem#523.
"""

from datetime import datetime

import pytest

from opennem.api.data.schema import DataMetric
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkNEM


@pytest.mark.parametrize("query_type", [QueryType.DATA, QueryType.FACILITY])
def test_power_hourly_uses_avg(query_type):
    """1h power: avg(generated) on the base unit_intervals table."""
    sql, _, _ = get_timeseries_query(
        query_type=query_type,
        network=NetworkNEM,
        metrics=[DataMetric.POWER, DataMetric.ENERGY],
        interval=Interval.HOUR,
        date_start=datetime(2025, 4, 22, 14, 0),
        date_end=datetime(2025, 4, 22, 15, 0),
        unit_code=["WAUBRAWF"],
    )
    assert "avg(generated)" in sql
    assert "sum(generated)" not in sql
    assert "sum(energy)" in sql  # energy is still summed
    assert "FROM unit_intervals " in sql  # base table for hourly


@pytest.mark.parametrize("query_type", [QueryType.DATA, QueryType.FACILITY])
def test_power_daily_uses_interval_weighted_avg(query_type):
    """1d power: sum(generated) / sum(interval_count) against the daily MV.

    The daily MV stores generated as sum(generated) per day. A weighted average by
    interval_count gives the correct mean power over the queried range, including
    partial first/last days.
    """
    sql, _, _ = get_timeseries_query(
        query_type=query_type,
        network=NetworkNEM,
        metrics=[DataMetric.POWER, DataMetric.ENERGY],
        interval=Interval.DAY,
        date_start=datetime(2025, 4, 22, 0, 0),
        date_end=datetime(2025, 4, 23, 0, 0),
        unit_code=["WAUBRAWF"],
    )
    assert "sum(generated) / nullIf(sum(interval_count), 0)" in sql
    assert "FROM unit_intervals_daily_mv" in sql
    assert "sum(energy)" in sql


@pytest.mark.parametrize("query_type", [QueryType.DATA, QueryType.FACILITY])
@pytest.mark.parametrize("interval", [Interval.WEEK, Interval.MONTH, Interval.QUARTER, Interval.YEAR])
def test_power_multi_day_uses_interval_weighted_avg(query_type, interval):
    """Week / month / quarter / year all aggregate from the daily MV with weighted avg."""
    sql, _, _ = get_timeseries_query(
        query_type=query_type,
        network=NetworkNEM,
        metrics=[DataMetric.POWER],
        interval=interval,
        date_start=datetime(2025, 1, 1, 0, 0),
        date_end=datetime(2025, 6, 1, 0, 0),
    )
    assert "sum(generated) / nullIf(sum(interval_count), 0)" in sql
    assert "FROM unit_intervals_daily_mv" in sql
