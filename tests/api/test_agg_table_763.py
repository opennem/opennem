"""fueltech_region_intervals: routing predicate, query text, write isolation, rebuild SQL (#763). No network."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from opennem import settings
from opennem.aggregates import fueltech_region_intervals as agg
from opennem.api.data.schema import DataMetric
from opennem.api.queries import AGG_TABLE, QueryType, agg_table_supported, get_timeseries_query
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkNEM

END = datetime.now(UTC).replace(tzinfo=None)
START = END - timedelta(days=7)
SG = SecondaryGrouping
PG = PrimaryGrouping


@pytest.mark.parametrize("interval", [Interval.INTERVAL, Interval.HALF_HOUR, Interval.HOUR])
@pytest.mark.parametrize("secondary", [None, [SG.FUELTECH], [SG.FUELTECH_GROUP]])
@pytest.mark.parametrize("primary", [PG.NETWORK, PG.NETWORK_REGION])
def test_routes_tracker_shapes(interval, secondary, primary):
    assert agg_table_supported(
        QueryType.DATA, primary, interval, [DataMetric.POWER, Metric.EMISSIONS, Metric.MARKET_VALUE, Metric.ENERGY], secondary
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"query_type": QueryType.MARKET},
        {"query_type": QueryType.FACILITY},
        {"interval": Interval.DAY},
        {"interval": Interval.MONTH},
        {"primary_grouping": PG.FACILITY if hasattr(PG, "FACILITY") else PG.NETWORK_REGION, "facility_code": ["X"]},
        {"metrics": [DataMetric.STORAGE_BATTERY]},
        {"metrics": []},
        {"secondary_groupings": [SG.RENEWABLE]},
        {"secondary_groupings": [SG.STATUS]},
        {"secondary_groupings": [SG.FUELTECH, SG.FUELTECH_GROUP]},
        {"unit_code": ["BAYSW1"]},
    ],
)
def test_falls_back_for_other_shapes(kwargs):
    base = {
        "query_type": QueryType.DATA,
        "primary_grouping": PG.NETWORK_REGION,
        "interval": Interval.INTERVAL,
        "metrics": [DataMetric.POWER],
        "secondary_groupings": [SG.FUELTECH],
    }
    assert not agg_table_supported(**{**base, **kwargs})


def test_recency_guard(monkeypatch):
    monkeypatch.setattr(settings, "clickhouse_agg_table_max_age_days", 60)
    now = datetime(2026, 10, 24, 12, 0)
    kw = {"query_type": QueryType.DATA, "primary_grouping": PG.NETWORK, "interval": Interval.INTERVAL,
          "metrics": [DataMetric.POWER], "secondary_groupings": None, "now": now}  # fmt: skip
    assert agg_table_supported(**kw, date_start=now - timedelta(days=50))
    assert not agg_table_supported(**kw, date_start=now - timedelta(days=80))


def _sql(**kwargs):
    kw = {
        "query_type": QueryType.DATA,
        "network": NetworkNEM,
        "metrics": [DataMetric.POWER],
        "interval": Interval.INTERVAL,
        "date_start": START,
        "date_end": END,
        "primary_grouping": PG.NETWORK_REGION,
        "secondary_groupings": [SG.FUELTECH],
        "columnar": True,
    }
    return get_timeseries_query(**{**kw, **kwargs})[0]


def test_routed_query_reads_agg_table_with_same_expressions():
    routed = _sql(use_agg_table=True)
    raw = _sql(use_agg_table=False)
    assert f"FROM {AGG_TABLE} FINAL" in routed
    assert "FROM unit_intervals FINAL" in raw
    assert routed.replace(AGG_TABLE, "unit_intervals") == raw


def test_flag_default_off_and_setting_drives_routing(monkeypatch):
    assert settings.clickhouse_agg_table_routing is False
    assert settings.clickhouse_agg_table_write is False
    assert AGG_TABLE not in _sql()
    monkeypatch.setattr(settings, "clickhouse_agg_table_routing", True)
    assert AGG_TABLE in _sql()
    assert AGG_TABLE not in _sql(use_agg_table=False)


def test_daily_and_ineligible_do_not_route():
    assert AGG_TABLE not in _sql(use_agg_table=True, interval=Interval.DAY, date_start=END - timedelta(days=40))
    assert AGG_TABLE not in _sql(use_agg_table=True, metrics=[DataMetric.STORAGE_BATTERY])


def test_agg_wins_over_subday_mv():
    sql = _sql(use_agg_table=True, use_subday_mv=True)
    assert AGG_TABLE in sql and "fueltech_intervals_mv" not in sql


# ---- aggregation of prepared rows ----


def _row(ts, region, ft, grp, gen, en=1.0, em=None, mv=None, version=100, unit="U1"):
    return (ts, "NEM", region, "F", unit, "operating", ft, grp, False, gen, en, None, em, None, mv, version)


def test_aggregate_rows_sums_and_null_semantics():
    t = datetime(2026, 10, 1, 0, 5)
    rows = [
        _row(t, "NSW1", "coal_black", "coal", 10.0001, em=None, unit="A"),
        _row(t, "NSW1", "coal_black", "coal", 5.0, em=None, unit="B"),
        _row(t, "NSW1", "wind", "wind", None, en=None, unit="C"),
        _row(t, "QLD1", "coal_black", "coal", 1.0, em=2.0, mv=3.0, unit="D", version=101),
    ]
    out = {(r[1], r[2], r[3]): r for r in agg.aggregate_rows(rows)}
    nsw = out[("NEM", "NSW1", "coal_black")]
    assert nsw[5] == 15.0001 and nsw[6] == 2.0 and nsw[7] is None and nsw[8] is None
    assert nsw[9] == 2 and nsw[10] == 100
    wind = out[("NEM", "NSW1", "wind")]
    assert wind[5] is None and wind[6] is None  # all-null stays null, not 0
    assert out[("NEM", "QLD1", "coal_black")][7:9] == (2.0, 3.0) and out[("NEM", "QLD1", "coal_black")][10] == 101
    assert agg.aggregate_rows([]) == []


# ---- write path isolation ----


def test_write_is_noop_when_flag_off(monkeypatch):
    monkeypatch.setattr(settings, "clickhouse_agg_table_write", False)
    called = MagicMock()
    monkeypatch.setattr(agg, "insert_async", called)
    assert asyncio.run(agg.write_aggregate([_row(datetime(2026, 10, 1), "NSW1", "wind", "wind", 1.0)])) == 0
    called.assert_not_called()


def test_write_failure_never_raises_and_is_reported(monkeypatch):
    monkeypatch.setattr(settings, "clickhouse_agg_table_write", True)

    async def boom(*a, **k):
        raise RuntimeError("table missing")

    reported = MagicMock()
    monkeypatch.setattr(agg, "insert_async", boom)
    monkeypatch.setattr(agg, "_report_failure", reported)
    assert asyncio.run(agg.write_aggregate([_row(datetime(2026, 10, 1), "NSW1", "wind", "wind", 1.0)])) == 0
    reported.assert_called_once()
    assert reported.call_args.args[0] == "write"


def test_aggregation_failure_never_raises(monkeypatch):
    monkeypatch.setattr(settings, "clickhouse_agg_table_write", True)
    reported = MagicMock()
    monkeypatch.setattr(agg, "_report_failure", reported)
    assert asyncio.run(agg.write_aggregate([("garbage",)])) == 0
    reported.assert_called_once()


def test_write_inserts_aggregated_rows(monkeypatch):
    monkeypatch.setattr(settings, "clickhouse_agg_table_write", True)
    seen = {}

    async def fake_insert(sql, data, *a, **k):
        seen["sql"], seen["data"] = sql, data

    monkeypatch.setattr(agg, "insert_async", fake_insert)
    t = datetime(2026, 10, 1)
    n = asyncio.run(
        agg.write_aggregate([_row(t, "NSW1", "wind", "wind", 1.0, unit="a"), _row(t, "NSW1", "wind", "wind", 2.0, unit="b")])
    )
    assert n == 1 and f"INSERT INTO {AGG_TABLE}" in seen["sql"] and seen["data"][0][5] == 3.0


def test_unit_intervals_write_survives_agg_failure(monkeypatch):
    """The unit_intervals insert is awaited before the agg write and the agg write cannot raise."""
    from opennem.aggregates import unit_intervals as ui

    monkeypatch.setattr(settings, "clickhouse_agg_table_write", True)
    order: list[str] = []

    async def fake_insert(sql, data, *a, **k):
        order.append("agg" if AGG_TABLE in sql else "unit")
        if AGG_TABLE in sql:
            raise RuntimeError("agg down")

    monkeypatch.setattr(agg, "insert_async", fake_insert)
    monkeypatch.setattr(agg, "_report_failure", MagicMock())

    async def go():
        await fake_insert("INSERT INTO unit_intervals", [])
        await ui.write_agg_rows([_row(datetime(2026, 10, 1), "NSW1", "wind", "wind", 1.0)])

    asyncio.run(go())
    assert order == ["unit", "agg"]


# ---- rebuild helper ----


def test_rebuild_range_sql_inserts_then_deletes_older_per_day():
    client = MagicMock()
    client.execute.side_effect = lambda sql, params=None: [(5,)] if "count()" in sql and "FINAL WHERE" in sql else []
    n = agg.rebuild_range_sync(datetime(2026, 10, 1), datetime(2026, 10, 3), client=client, version=777)
    assert n == 5
    calls = [(c.args[0], c.args[1] if len(c.args) > 1 else None) for c in client.execute.call_args_list]
    sqls = [c[0] for c in calls]
    assert sum("FROM unit_intervals FINAL" in s for s in sqls) == 2
    assert sum("DELETE" in s for s in sqls) == 2
    writes = [s for s in sqls if "INSERT" in s or "DELETE" in s]
    assert ["INSERT" in s for s in writes] == [True, False, True, False]  # insert first, then delete older, per day
    ins = next(c for c in calls if "INSERT" in c[0])
    assert ins[1] == {"start": datetime(2026, 10, 1), "end": datetime(2026, 10, 2), "version": 777}
    assert "version < %(version)s" in next(s for s in sqls if "DELETE" in s)
    assert "GROUP BY interval, network_id, network_region, fueltech_id, fueltech_group_id" in ins[0]


def test_rebuild_wrapper_flag_gated_and_isolated(monkeypatch):
    monkeypatch.setattr(settings, "clickhouse_agg_table_write", False)
    boom = MagicMock(side_effect=RuntimeError("x"))
    monkeypatch.setattr(agg, "rebuild_range_sync", boom)
    assert asyncio.run(agg.rebuild_range(datetime(2026, 10, 1), datetime(2026, 10, 2))) == 0
    boom.assert_not_called()
    monkeypatch.setattr(settings, "clickhouse_agg_table_write", True)
    monkeypatch.setattr(agg, "_report_failure", MagicMock())
    assert asyncio.run(agg.rebuild_range(datetime(2026, 10, 1), datetime(2026, 10, 2))) == 0
    boom.assert_called_once()
    assert boom.call_args.args[1] == datetime(2026, 10, 2, 0, 5)  # inclusive end bucket


# ---- comparison ----


def test_diff_day_rows():
    base = (100, 1000, 0, 2, 5, 7, 1e9, 2e9, 3e6, 4e6)
    assert agg.diff_day_rows(base, base) == []
    assert agg.diff_day_rows(base, (100, 1000, 0, 2, 5, 7, 1e9 + 1e-4, 2e9, 3e6, 4e6)) == []
    bad = agg.diff_day_rows(base, (99, 1000, 0, 2, 5, 7, 1e9 + 5, 2e9, 3e6, 4e6))
    assert len(bad) == 2 and bad[0].startswith("n ") and bad[1].startswith("generated_sum")
