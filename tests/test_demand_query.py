"""Monthly demand query must aggregate the daily MV, not the monthly MV.

market_summary_monthly_mv auto-populates per-batch and held partial-month
aggregates (eg NSW1 May-2026 demand 373 GWh vs the true 5859), which made the
"all" view disagree with the daily-summed "1 year" view on price/demand. The
fix routes the monthly demand query through the backfilled, correct
market_summary_daily_mv. This guards against a regression back to the rotting MV.
"""

from datetime import datetime

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.time import get_interval
from opennem.queries.demand import network_demand_clickhouse_query
from opennem.schema.network import NetworkNEM


def _sql(interval_human: str) -> str:
    time_series = OpennemExportSeries(
        start=datetime(1999, 1, 1),
        end=datetime(2026, 5, 31),
        network=NetworkNEM,
        interval=get_interval(interval_human),
        period=None,
    )
    return str(network_demand_clickhouse_query(time_series=time_series, network_region="NSW1"))


def test_monthly_demand_uses_daily_mv_not_monthly_mv() -> None:
    sql = _sql("1M")
    assert "market_summary_daily_mv" in sql, "monthly demand must read the daily MV"
    assert "market_summary_monthly_mv" not in sql, "must NOT read the rotting monthly MV (partial aggregates)"


def test_monthly_demand_sums_daily_columns_by_month() -> None:
    sql = _sql("1M")
    assert "sum(demand_total_energy_daily)" in sql
    assert "sum(demand_total_market_value_daily)" in sql
    assert "toStartOfMonth(date)" in sql
    assert "GROUP BY" in sql


def test_daily_demand_still_uses_daily_mv() -> None:
    sql = _sql("1d")
    assert "market_summary_daily_mv" in sql
    assert "demand_total_energy_daily" in sql
