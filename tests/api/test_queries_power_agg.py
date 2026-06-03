"""Lock the per-interval aggregation for DataMetric.POWER.

POWER (MW) is an instantaneous rate, so the SQL must:
  1. Sum across units within each raw 5-minute interval (inner CTE), giving
     the per-interval network-aggregate power at each 5-min slice.
  2. Average those per-interval values across the queried bucket (outer SELECT).

ENERGY/EMISSIONS/MARKET_VALUE remain summed at both stages because they are
cumulative quantities.

Regression tests for opennem#523 and opennem#525.
"""

from datetime import datetime

import pytest

from opennem.api.data.schema import DataMetric
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.core.grouping import SecondaryGrouping
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkNEM


@pytest.mark.parametrize("query_type", [QueryType.DATA, QueryType.FACILITY])
def test_power_hourly_uses_avg_of_inner_sum(query_type):
    """1h power: inner sums across units, outer averages across raw 5-min intervals."""
    sql, _, _ = get_timeseries_query(
        query_type=query_type,
        network=NetworkNEM,
        metrics=[DataMetric.POWER, DataMetric.ENERGY],
        interval=Interval.HOUR,
        date_start=datetime(2025, 4, 22, 14, 0),
        date_end=datetime(2025, 4, 22, 15, 0),
        unit_code=["WAUBRAWF"],
    )
    # Inner pre-aggregates per raw 5-min
    assert "sum(generated) AS generated_sum" in sql
    assert "FROM unit_intervals FINAL" in sql
    # Outer averages the per-interval sums
    assert "round(avg(generated_sum), 6) AS power" in sql
    # Energy still sums end-to-end
    assert "sum(energy) AS energy_sum" in sql
    assert "round(sum(energy_sum), 6) AS energy" in sql


@pytest.mark.parametrize("query_type", [QueryType.DATA, QueryType.FACILITY])
@pytest.mark.parametrize("interval", [Interval.DAY, Interval.WEEK, Interval.MONTH, Interval.QUARTER, Interval.YEAR])
def test_power_multi_bucket_uses_same_shape(query_type, interval):
    """Day / week / month / quarter / year all use the same CTE structure as hourly.

    The bucket function differs (toStartOfDay/Week/Month/etc) but the inner
    pre-aggregation and outer avg() are identical to the hourly path.
    """
    sql, _, _ = get_timeseries_query(
        query_type=query_type,
        network=NetworkNEM,
        metrics=[DataMetric.POWER],
        interval=interval,
        date_start=datetime(2025, 1, 1, 0, 0),
        date_end=datetime(2025, 6, 1, 0, 0),
    )
    assert "sum(generated) AS generated_sum" in sql
    assert "FROM unit_intervals FINAL" in sql
    assert "round(avg(generated_sum), 6) AS power" in sql
    # Make sure we no longer fall back to the buggy daily MV path
    assert "unit_intervals_daily_mv" not in sql


def test_network_aggregate_power_collapses_units_in_inner():
    """Network-aggregate POWER must not average across units — it sums them in the inner CTE.

    Regression for the bug found by the e2e harness: pre-refactor the outer `avg(generated)`
    averaged across both intervals and units, returning ~50 MW for NEM 1h (true value ~26500 MW).
    """
    sql, _, _ = get_timeseries_query(
        query_type=QueryType.DATA,
        network=NetworkNEM,
        metrics=[DataMetric.POWER],
        interval=Interval.HOUR,
        date_start=datetime(2025, 4, 22, 14, 0),
        date_end=datetime(2025, 4, 22, 15, 0),
    )
    # Inner sums across units → unit dimension collapses at the 5-min level
    assert "sum(generated) AS generated_sum" in sql
    # Outer averages the per-5min network totals → network-aggregate avg over the bucket
    assert "round(avg(generated_sum), 6) AS power" in sql


@pytest.mark.parametrize(
    ("grouping", "col"),
    [
        (SecondaryGrouping.FUELTECH, "fueltech_id"),
        (SecondaryGrouping.FUELTECH_GROUP, "fueltech_group_id"),
        (SecondaryGrouping.STATUS, "status_id"),
        (SecondaryGrouping.RENEWABLE, "renewable"),
    ],
)
def test_secondary_grouping_emits_column(grouping, col):
    """Every SecondaryGrouping must wire its source column into the query + column_names.

    Regression for opennem#539: secondary_grouping=status 500'd because the STATUS
    branch was missing from the query builder and the timeseries label dicts, so
    status_id was never grouped/selected and label-building raised KeyError.
    """
    sql, _, column_names = get_timeseries_query(
        query_type=QueryType.DATA,
        network=NetworkNEM,
        metrics=[DataMetric.ENERGY],
        interval=Interval.DAY,
        date_start=datetime(2026, 5, 22, 0, 0),
        date_end=datetime(2026, 5, 23, 0, 0),
        secondary_groupings=[grouping],
    )
    # source column is grouped/selected in the SQL
    assert col in sql
    # output column name is present for callers to zip with row tuples
    assert grouping.value in column_names
