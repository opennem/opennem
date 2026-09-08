"""Day-or-coarser buckets are served from the daily materialised views.

Sub-daily buckets scan the raw 5-minute tables; anything from 1d up reads
`fueltech_intervals_daily_mv` / `unit_intervals_daily_mv` / `market_summary_daily_mv`
for whole days, unioned with the raw table for any partial day at either end of the
request. Locks in:

* table selection per query type, interval, grouping and filter
* metric plan shapes on the daily path (sum→sum, avg→sum/merged slot bitmaps, ratios)
* whole-day / edge splitting and the raw fallbacks (STATUS grouping, sub-day ranges)
"""

from datetime import date, datetime

import pytest

from opennem.api.data.schema import DataMetric
from opennem.api.queries import (
    DAILY_INTERVALS,
    DATA_METRIC_PLANS,
    DATA_METRIC_PLANS_DAILY,
    MARKET_METRIC_PLANS,
    MARKET_METRIC_PLANS_DAILY,
    QueryType,
    _daily_split,
    get_timeseries_query,
)
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkNEM

START = datetime(2025, 1, 1, 0, 0)
END = datetime(2025, 6, 1, 0, 0)


def _data(interval: Interval, metrics=None, **kwargs):
    kwargs.setdefault("date_start", START)
    kwargs.setdefault("date_end", END)
    return get_timeseries_query(
        query_type=QueryType.DATA,
        network=NetworkNEM,
        metrics=metrics or [DataMetric.ENERGY],
        interval=interval,
        **kwargs,
    )


def _market(interval: Interval, metrics, **kwargs):
    kwargs.setdefault("date_start", START)
    kwargs.setdefault("date_end", END)
    return get_timeseries_query(
        query_type=QueryType.MARKET,
        network=NetworkNEM,
        metrics=metrics,
        interval=interval,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# table selection


def test_daily_intervals_cover_every_day_or_coarser_bucket():
    assert DAILY_INTERVALS == {
        Interval.DAY,
        Interval.WEEK,
        Interval.MONTH,
        Interval.QUARTER,
        Interval.SEASON,
        Interval.YEAR,
        Interval.FINANCIAL_YEAR,
    }
    assert Interval.INTERVAL not in DAILY_INTERVALS
    assert Interval.HOUR not in DAILY_INTERVALS


@pytest.mark.parametrize("interval", [Interval.INTERVAL, Interval.HOUR])
def test_sub_daily_reads_raw_tables(interval):
    sql, params, _ = _data(interval)
    assert "FROM unit_intervals FINAL" in sql
    assert "_daily_mv" not in sql
    assert "UNION ALL" not in sql
    assert "interval AS raw_interval" in sql
    assert params["date_start"] == START and params["date_end"] == END

    sql, _, _ = _market(interval, [Metric.PRICE])
    assert "FROM market_summary FINAL" in sql


@pytest.mark.parametrize("interval", sorted(DAILY_INTERVALS))
def test_daily_or_coarser_reads_daily_views(interval):
    sql, params, _ = _data(interval)
    assert "FROM fueltech_intervals_daily_mv FINAL" in sql
    assert "FROM unit_intervals FINAL" not in sql
    assert "UNION ALL" not in sql  # midnight-aligned: no edge days
    assert "toDateTime64(date, 3) AS raw_interval" in sql
    assert "date >= %(day_start)s AND date < %(day_end)s" in sql
    assert params["day_start"] == date(2025, 1, 1)
    assert params["day_end"] == date(2025, 6, 1)
    assert "date_start" not in params and "date_end" not in params

    sql, _, _ = _market(interval, [Metric.PRICE])
    assert "FROM market_summary_daily_mv FINAL" in sql


def test_facility_query_uses_unit_daily_view():
    sql, _, cols = get_timeseries_query(
        query_type=QueryType.FACILITY,
        network=NetworkNEM,
        metrics=[DataMetric.POWER, DataMetric.ENERGY],
        interval=Interval.DAY,
        date_start=START,
        date_end=END,
        unit_code=["BAYSW1"],
    )
    assert "FROM unit_intervals_daily_mv FINAL" in sql
    assert "GROUP BY raw_interval, facility_code, unit_code" in sql
    assert cols[:4] == ["interval", "network", "facility_code", "unit_code"]


@pytest.mark.parametrize(
    "grouping, expected_table",
    [
        (SecondaryGrouping.FUELTECH, "fueltech_intervals_daily_mv"),
        (SecondaryGrouping.FUELTECH_GROUP, "fueltech_intervals_daily_mv"),
        # renewable flag lives per unit — only the unit view carries it
        (SecondaryGrouping.RENEWABLE, "unit_intervals_daily_mv"),
    ],
)
def test_secondary_grouping_picks_view_with_the_dimension(grouping, expected_table):
    sql, _, cols = _data(Interval.MONTH, secondary_groupings=[grouping])
    assert f"FROM {expected_table} FINAL" in sql
    assert grouping.value in cols


def test_status_grouping_stays_on_raw_table():
    """The unit view stores one status per unit-day, so intraday status changes need raw rows."""
    sql, params, cols = _data(Interval.MONTH, secondary_groupings=[SecondaryGrouping.STATUS])
    assert "FROM unit_intervals FINAL" in sql
    assert "_daily_mv" not in sql
    assert "status" in cols
    assert params["date_start"] == START


@pytest.mark.parametrize("kwargs", [{"facility_code": ["BAYSW"]}, {"unit_code": ["BAYSW1"]}])
def test_unit_level_filters_pick_unit_daily_view(kwargs):
    sql, params, _ = _data(Interval.DAY, **kwargs)
    assert "FROM unit_intervals_daily_mv FINAL" in sql
    key = next(iter(kwargs))
    assert f"{key} in %({key})s" in sql
    assert params[key] == tuple(kwargs[key])


def test_region_grouping_and_fueltech_filter_on_daily_view():
    sql, params, cols = _data(
        Interval.WEEK,
        primary_grouping=PrimaryGrouping.NETWORK_REGION,
        secondary_groupings=[SecondaryGrouping.FUELTECH],
        network_region="NSW1",
        fueltech=["coal_black"],
    )
    assert "FROM fueltech_intervals_daily_mv FINAL" in sql
    assert "network_region = %(network_region)s" in sql
    assert "fueltech_id in %(fueltech)s" in sql
    assert params["network_region"] == "NSW1"
    assert cols == ["interval", "network", "network_region", "fueltech", "energy"]


# ---------------------------------------------------------------------------
# metric plans on the daily path


def test_data_metric_plans_daily():
    sql, _, _ = _data(
        Interval.MONTH,
        metrics=[
            DataMetric.POWER,
            DataMetric.ENERGY,
            DataMetric.EMISSIONS,
            DataMetric.MARKET_VALUE,
            DataMetric.STORAGE_BATTERY,
        ],
    )
    # MW: bucket sum / count of raw intervals with a value (never avg across rows)
    assert "groupBitmapMerge(generated_slots) AS generated_sum_n" in sql
    assert "round(sum(generated_sum) / nullIf(sum(generated_sum_n), 0), 6) AS power" in sql
    # MWh-class: sum of daily sums
    assert "round(sum(energy_sum), 6) AS energy" in sql
    assert "round(sum(emissions_sum), 6) AS emissions" in sql
    assert "round(sum(market_value_sum), 6) AS market_value" in sql
    # SoC: daily view already holds the coalesced sum + non-null count
    assert "sum(energy_storage_sum) AS energy_storage_sum" in sql
    assert "sum(energy_storage_count) AS energy_storage_count" in sql
    assert "round(sum(energy_storage_sum) / nullIf(sum(energy_storage_count), 0), 6) AS storage_battery" in sql
    assert "avg(" not in sql
    assert "coalesce(" not in sql


def test_market_metric_plans_daily_mw_and_mwh():
    sql, _, _ = _market(
        Interval.MONTH,
        [
            Metric.PRICE,
            Metric.DEMAND,
            Metric.DEMAND_ENERGY,
            Metric.CURTAILMENT,
            Metric.CURTAILMENT_ENERGY,
            Metric.FLOW_IMPORTS,
            Metric.FLOW_IMPORTS_ENERGY,
        ],
    )
    assert "sum(price_sum) AS price_sum_inner" in sql
    assert "sum(price_count) AS price_count_inner" in sql
    assert "round(sum(price_sum_inner) / nullIf(sum(price_count_inner), 0), 6) AS price" in sql
    assert "sum(demand_sum) AS demand_sum_inner" in sql
    assert "groupBitmapMerge(demand_slots) AS demand_sum_inner_n" in sql
    assert "round(sum(demand_sum_inner) / nullIf(sum(demand_sum_inner_n), 0), 6) AS demand" in sql
    assert "round(sum(demand_energy_sum), 6) AS demand_energy" in sql
    assert "sum(curtailment_total_daily) AS curtailment_total_inner" in sql
    assert "round(sum(curtailment_total_inner) / nullIf(sum(curtailment_total_inner_n), 0), 6) AS curtailment" in sql
    assert "round(sum(curtailment_energy_total_sum), 6) AS curtailment_energy" in sql
    # flows: MWh/day summed, ×12 recovers MW per 5-min interval
    assert "sum(energy_imports_daily) AS energy_imports_sum_inner" in sql
    assert "round(sum(energy_imports_sum_inner) * 12 / nullIf(sum(energy_imports_sum_inner_n), 0), 6) AS flow_imports" in sql
    assert "round(sum(energy_imports_sum_inner), 6) AS flow_imports_energy" in sql
    # shared inner alias emitted once
    assert sql.count("sum(energy_imports_daily) AS energy_imports_sum_inner") == 1
    assert "avg(" not in sql


def test_market_proportions_daily_divide_bucket_sums():
    sql, _, _ = _market(
        Interval.YEAR,
        [Metric.RENEWABLE_PROPORTION, Metric.RENEWABLE_WITH_STORAGE_PROPORTION, Metric.GENERATION_RENEWABLE],
    )
    assert "sum(generation_renewable_sum) AS gr_sum_inner" in sql
    assert "sum(generation_renewable_with_storage_sum) AS grws_sum_inner" in sql
    assert "sum(demand_gross_sum) AS dg_sum_inner" in sql
    assert sql.count("AS dg_sum_inner") == 1
    assert (
        "if(sum(dg_sum_inner) > 0, round((sum(gr_sum_inner) / sum(dg_sum_inner)) * 100, 2), NULL) AS renewable_proportion" in sql
    )
    assert (
        "if(sum(dg_sum_inner) > 0, round((sum(grws_sum_inner) / sum(dg_sum_inner)) * 100, 2), NULL) "
        "AS renewable_with_storage_proportion" in sql
    )
    assert "round(sum(gr_sum_inner) / nullIf(sum(gr_sum_inner_n), 0), 6) AS generation_renewable" in sql


def test_every_raw_metric_has_a_daily_plan_with_edge_expressions():
    assert set(DATA_METRIC_PLANS_DAILY) == set(DATA_METRIC_PLANS)
    assert set(MARKET_METRIC_PLANS_DAILY) == set(MARKET_METRIC_PLANS)
    for plans in (DATA_METRIC_PLANS_DAILY, MARKET_METRIC_PLANS_DAILY):
        for metric, plan in plans.items():
            assert plan.edge is not None, metric
            assert set(plan.edge) == set(plan.inner), metric


# ---------------------------------------------------------------------------
# whole-day / edge splitting


def test_split_midnight_aligned_has_no_edges():
    split = _daily_split(datetime(2025, 1, 1), datetime(2025, 6, 1))
    assert split is not None
    assert (split.day_start, split.day_end) == (date(2025, 1, 1), date(2025, 6, 1))
    assert split.edges == ()


def test_split_intraday_bounds_yield_edges():
    split = _daily_split(datetime(2025, 5, 2, 14, 35), datetime(2025, 6, 1, 12, 0))
    assert split is not None
    assert (split.day_start, split.day_end) == (date(2025, 5, 3), date(2025, 6, 1))
    assert split.edges == (
        (datetime(2025, 5, 2, 14, 35), datetime(2025, 5, 3)),
        (datetime(2025, 6, 1), datetime(2025, 6, 1, 12, 0)),
    )


def test_split_without_a_whole_day_is_none():
    assert _daily_split(datetime(2025, 5, 2, 1, 0), datetime(2025, 5, 2, 23, 0)) is None
    assert _daily_split(datetime(2025, 5, 2, 1, 0), datetime(2025, 5, 3, 23, 0)) is None
    assert _daily_split(datetime(2025, 5, 2, 0, 0), datetime(2025, 5, 3, 0, 0)) is not None


def test_sub_day_range_falls_back_to_raw():
    sql, params, _ = _data(Interval.DAY, date_start=datetime(2025, 5, 2, 1, 0), date_end=datetime(2025, 5, 2, 23, 0))
    assert "FROM unit_intervals FINAL" in sql
    assert "_daily_mv" not in sql
    assert params["date_start"] == datetime(2025, 5, 2, 1, 0)


def test_live_tail_comes_from_raw_table_union():
    """A live request capped at the last settled interval reads today from the raw table."""
    sql, params, _ = _data(
        Interval.DAY,
        metrics=[DataMetric.POWER, DataMetric.ENERGY],
        date_start=datetime(2025, 5, 2),
        date_end=datetime(2025, 6, 1, 14, 35),
        secondary_groupings=[SecondaryGrouping.FUELTECH],
    )
    assert "FROM fueltech_intervals_daily_mv FINAL" in sql
    assert "UNION ALL" in sql
    assert "FROM unit_intervals FINAL" in sql
    assert "(interval >= %(edge0_start)s AND interval < %(edge0_end)s)" in sql
    assert "edge1_start" not in sql
    assert params["day_start"] == date(2025, 5, 2)
    assert params["day_end"] == date(2025, 6, 1)
    assert params["edge0_start"] == datetime(2025, 6, 1)
    assert params["edge0_end"] == datetime(2025, 6, 1, 14, 35)
    # edge rows carry the same aliases in the same order as the view rows
    assert (
        "sum(generated) AS generated_sum, if(sum(generated) IS NOT NULL, 1, 0) AS generated_sum_n, sum(energy) AS energy_sum"
        in sql
    )
    assert "GROUP BY raw_interval, fueltech_id" in sql
    # filters apply to both halves
    assert sql.count("network_id in %(network)s") == 2


def test_both_edges_union_with_or_range():
    sql, params, _ = _market(
        Interval.DAY,
        [Metric.DEMAND, Metric.PRICE],
        date_start=datetime(2025, 5, 2, 14, 35),
        date_end=datetime(2025, 6, 1, 12, 0),
        primary_grouping=PrimaryGrouping.NETWORK_REGION,
        network_region="NSW1",
    )
    assert "FROM market_summary_daily_mv FINAL" in sql
    assert "FROM market_summary FINAL" in sql
    head = "(interval >= %(edge0_start)s AND interval < %(edge0_end)s)"
    tail = "(interval >= %(edge1_start)s AND interval < %(edge1_end)s)"
    assert f"({head} OR {tail})" in sql
    assert sql.count("network_region = %(network_region)s") == 2
    assert "sum(demand) AS demand_sum_inner, if(sum(demand) IS NOT NULL, 1, 0) AS demand_sum_inner_n" in sql
    assert "sum(price) AS price_sum_inner, countIf(price IS NOT NULL) AS price_count_inner" in sql
    assert params["edge1_end"] == datetime(2025, 6, 1, 12, 0)
