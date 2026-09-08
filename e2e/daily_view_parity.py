"""Raw-table vs daily-view parity for day-or-coarser API buckets.

Builds every case twice with `get_timeseries_query` — once as shipped (daily views
for 1d+ buckets) and once with the daily path disabled (raw `unit_intervals` /
`market_summary`) — runs both against the configured ClickHouse, and diffs the
result sets key-by-key. Also reports wall time for each, which is the point of the
views: the raw path is the ~70s/4y query the tracker was hitting.

Usage:
    uv run python e2e/daily_view_parity.py                # default matrix, ch from ENV
    uv run python e2e/daily_view_parity.py --filter market
    uv run python e2e/daily_view_parity.py --rel-tol 1e-6 --abs-tol 1e-3

Windows are midnight/month aligned so both paths see identical day sets; the only
designed divergence is a non-midnight `date_end`, where the view path includes the
whole final day (the raw path returns a partial bucket).
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import opennem.api.queries as queries
from opennem.api.data.schema import DataMetric
from opennem.api.queries import QueryType, get_timeseries_query
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse.client import get_clickhouse_client
from opennem.schema.network import NetworkNEM, NetworkWEM

Y1 = (datetime(2025, 6, 1), datetime(2026, 6, 1))
Y3 = (datetime(2023, 6, 1), datetime(2026, 6, 1))
D30 = (datetime(2026, 4, 1), datetime(2026, 5, 1))

DATA_ALL = [DataMetric.POWER, DataMetric.ENERGY, DataMetric.EMISSIONS, DataMetric.MARKET_VALUE, DataMetric.STORAGE_BATTERY]
MARKET_ALL = [
    Metric.PRICE,
    Metric.DEMAND,
    Metric.DEMAND_ENERGY,
    Metric.DEMAND_GROSS,
    Metric.DEMAND_GROSS_ENERGY,
    Metric.GENERATION_RENEWABLE,
    Metric.GENERATION_RENEWABLE_ENERGY,
    Metric.GENERATION_RENEWABLE_WITH_STORAGE,
    Metric.GENERATION_RENEWABLE_WITH_STORAGE_ENERGY,
    Metric.CURTAILMENT,
    Metric.CURTAILMENT_ENERGY,
    Metric.CURTAILMENT_SOLAR_UTILITY,
    Metric.CURTAILMENT_WIND,
    Metric.CURTAILMENT_SOLAR_UTILITY_ENERGY,
    Metric.CURTAILMENT_WIND_ENERGY,
    Metric.FLOW_IMPORTS,
    Metric.FLOW_EXPORTS,
    Metric.FLOW_IMPORTS_ENERGY,
    Metric.FLOW_EXPORTS_ENERGY,
    Metric.RENEWABLE_PROPORTION,
    Metric.RENEWABLE_WITH_STORAGE_PROPORTION,
]


@dataclass
class Case:
    id: str
    kwargs: dict[str, Any]


@dataclass
class Result:
    case: Case
    raw_ms: float
    view_ms: float
    raw_rows: int
    view_rows: int
    missing_in_view: int = 0
    missing_in_raw: int = 0
    mismatches: list[tuple[Any, str, Any, Any]] = field(default_factory=list)
    max_rel: float = 0.0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.mismatches and not self.missing_in_view and not self.missing_in_raw


def build_matrix() -> list[Case]:
    cases: list[Case] = []
    for net in (NetworkNEM, NetworkWEM):
        n = net.code
        region = "NSW1" if n == "NEM" else "WEM"
        for interval, window in [(Interval.DAY, D30), (Interval.WEEK, Y1), (Interval.MONTH, Y1)]:
            cases.append(
                Case(
                    f"data-{n}-{interval}-network",
                    {"query_type": QueryType.DATA, "network": net, "metrics": DATA_ALL, "interval": interval, "window": window},
                )
            )
            cases.append(
                Case(
                    f"data-{n}-{interval}-fueltech",
                    {
                        "query_type": QueryType.DATA,
                        "network": net,
                        "metrics": DATA_ALL,
                        "interval": interval,
                        "window": window,
                        "secondary_groupings": [SecondaryGrouping.FUELTECH],
                    },
                )
            )
            cases.append(
                Case(
                    f"data-{n}-{interval}-region-{region}-fueltech",
                    {
                        "query_type": QueryType.DATA,
                        "network": net,
                        "metrics": DATA_ALL,
                        "interval": interval,
                        "window": window,
                        "primary_grouping": PrimaryGrouping.NETWORK_REGION,
                        "secondary_groupings": [SecondaryGrouping.FUELTECH],
                        "network_region": region,
                    },
                )
            )
            cases.append(
                Case(
                    f"market-{n}-{interval}-network",
                    {
                        "query_type": QueryType.MARKET,
                        "network": net,
                        "metrics": MARKET_ALL,
                        "interval": interval,
                        "window": window,
                    },
                )
            )
            cases.append(
                Case(
                    f"market-{n}-{interval}-region-{region}",
                    {
                        "query_type": QueryType.MARKET,
                        "network": net,
                        "metrics": MARKET_ALL,
                        "interval": interval,
                        "window": window,
                        "primary_grouping": PrimaryGrouping.NETWORK_REGION,
                        "network_region": region,
                    },
                )
            )
        cases.append(
            Case(
                f"data-{n}-1M-regions-fueltech_group",
                {
                    "query_type": QueryType.DATA,
                    "network": net,
                    "metrics": DATA_ALL,
                    "interval": Interval.MONTH,
                    "window": Y1,
                    "primary_grouping": PrimaryGrouping.NETWORK_REGION,
                    "secondary_groupings": [SecondaryGrouping.FUELTECH_GROUP],
                },
            )
        )
        cases.append(
            Case(
                f"data-{n}-1M-renewable",
                {
                    "query_type": QueryType.DATA,
                    "network": net,
                    "metrics": DATA_ALL,
                    "interval": Interval.MONTH,
                    "window": Y1,
                    "secondary_groupings": [SecondaryGrouping.RENEWABLE],
                },
            )
        )
        cases.append(
            Case(
                f"data-{n}-1M-status",
                {
                    "query_type": QueryType.DATA,
                    "network": net,
                    "metrics": DATA_ALL,
                    "interval": Interval.MONTH,
                    "window": Y1,
                    "secondary_groupings": [SecondaryGrouping.STATUS],
                },
            )
        )
        cases.append(
            Case(
                f"data-{n}-1M-fueltech-filter-coal",
                {
                    "query_type": QueryType.DATA,
                    "network": net,
                    "metrics": DATA_ALL,
                    "interval": Interval.MONTH,
                    "window": Y1,
                    "fueltech": ["coal_black", "solar_rooftop"],
                    "secondary_groupings": [SecondaryGrouping.FUELTECH],
                },
            )
        )
        cases.append(
            Case(
                f"market-{n}-3M-regions",
                {
                    "query_type": QueryType.MARKET,
                    "network": net,
                    "metrics": MARKET_ALL,
                    "interval": Interval.QUARTER,
                    "window": Y3,
                    "primary_grouping": PrimaryGrouping.NETWORK_REGION,
                },
            )
        )
        cases.append(
            Case(
                f"market-{n}-1y-network",
                {"query_type": QueryType.MARKET, "network": net, "metrics": MARKET_ALL, "interval": Interval.YEAR, "window": Y3},
            )
        )
        cases.append(
            Case(
                f"market-{n}-season-network",
                {
                    "query_type": QueryType.MARKET,
                    "network": net,
                    "metrics": MARKET_ALL,
                    "interval": Interval.SEASON,
                    "window": Y3,
                },
            )
        )
        cases.append(
            Case(
                f"market-{n}-fy-network",
                {
                    "query_type": QueryType.MARKET,
                    "network": net,
                    "metrics": MARKET_ALL,
                    "interval": Interval.FINANCIAL_YEAR,
                    "window": Y3,
                },
            )
        )

    facility_metrics = [DataMetric.POWER, DataMetric.ENERGY, DataMetric.EMISSIONS, DataMetric.MARKET_VALUE]
    for unit in ("BAYSW1", "WAUBRAWF", "ERARING01"):
        for interval, window in [(Interval.DAY, D30), (Interval.MONTH, Y1)]:
            cases.append(
                Case(
                    f"facility-NEM-{unit}-{interval}",
                    {
                        "query_type": QueryType.FACILITY,
                        "network": NetworkNEM,
                        "metrics": facility_metrics,
                        "interval": interval,
                        "window": window,
                        "unit_code": [unit],
                    },
                )
            )
    cases.append(
        Case(
            "facility-NEM-battery-1d-soc",
            {
                "query_type": QueryType.FACILITY,
                "network": NetworkNEM,
                "metrics": [*facility_metrics, DataMetric.STORAGE_BATTERY],
                "interval": Interval.DAY,
                "window": D30,
                "facility_code": ["HPRG"],
            },
        )
    )
    cases.append(
        Case(
            "facility-WEM-COLLIE_G2-1M",
            {
                "query_type": QueryType.FACILITY,
                "network": NetworkWEM,
                "metrics": facility_metrics,
                "interval": Interval.MONTH,
                "window": Y1,
                "unit_code": ["COLLIE_G2"],
            },
        )
    )
    # 3-year data query: the tracker's "all" range shape
    cases.append(
        Case(
            "data-NEM-1M-fueltech-3y",
            {
                "query_type": QueryType.DATA,
                "network": NetworkNEM,
                "metrics": [DataMetric.ENERGY, DataMetric.EMISSIONS, DataMetric.MARKET_VALUE],
                "interval": Interval.MONTH,
                "window": Y3,
                "secondary_groupings": [SecondaryGrouping.FUELTECH],
            },
        )
    )
    return cases


def build(case: Case, force_raw: bool) -> tuple[str, dict, list[str]]:
    kw = dict(case.kwargs)
    date_start, date_end = kw.pop("window")
    saved = queries.DAILY_INTERVALS
    if force_raw:
        queries.DAILY_INTERVALS = frozenset()
    try:
        return get_timeseries_query(date_start=date_start, date_end=date_end, **kw)
    finally:
        queries.DAILY_INTERVALS = saved


def run_query(client, sql: str, params: dict) -> tuple[list[tuple], float]:
    t0 = time.perf_counter()
    rows = client.execute(sql, params)
    return rows, (time.perf_counter() - t0) * 1000


def keyed(rows: list[tuple], columns: list[str], n_metrics: int) -> dict[tuple, dict[str, Any]]:
    out: dict[tuple, dict[str, Any]] = {}
    n_key = len(columns) - n_metrics
    for row in rows:
        key = tuple(_norm_key(v) for v in row[:n_key])
        out[key] = dict(zip(columns[n_key:], row[n_key:], strict=True))
    return out


def _norm_key(v: Any) -> Any:
    # toStartOfMonth(DateTime64) returns Date on raw, toStartOfMonth(DateTime) Date on view;
    # toStartOfDay returns DateTime on both. Normalise to a date-or-datetime string.
    if isinstance(v, datetime):
        return v.isoformat()
    if hasattr(v, "isoformat"):
        return datetime(v.year, v.month, v.day).isoformat()
    return v


def close(a: Any, b: Any, rel_tol: float, abs_tol: float) -> tuple[bool, float]:
    if a is None and b is None:
        return True, 0.0
    if a is None or b is None:
        return False, math.inf
    if a == b:
        return True, 0.0
    diff = abs(a - b)
    scale = max(abs(a), abs(b))
    rel = diff / scale if scale else 0.0
    return (diff <= abs_tol or rel <= rel_tol), rel


def compare(case: Case, client, rel_tol: float, abs_tol: float) -> Result:
    sql_view, p_view, cols = build(case, force_raw=False)
    sql_raw, p_raw, cols_raw = build(case, force_raw=True)
    assert cols == cols_raw, (cols, cols_raw)
    assert "_daily_mv" not in sql_raw, case.id
    if "_daily_mv" not in sql_view:
        # Shipped path is raw-only for this shape (e.g. STATUS grouping) — nothing to compare.
        return Result(case, 0, 0, 0, 0, error="raw-only path")
    try:
        raw_rows, raw_ms = run_query(client, sql_raw, p_raw)
        view_rows, view_ms = run_query(client, sql_view, p_view)
    except Exception as e:  # noqa: BLE001
        return Result(case, 0, 0, 0, 0, error=f"{type(e).__name__}: {str(e)[:200]}")

    n_metrics = len(case.kwargs["metrics"])
    raw = keyed(raw_rows, cols, n_metrics)
    view = keyed(view_rows, cols, n_metrics)
    res = Result(case, raw_ms, view_ms, len(raw_rows), len(view_rows))
    res.missing_in_view = len(set(raw) - set(view))
    res.missing_in_raw = len(set(view) - set(raw))
    for key in set(raw) & set(view):
        for metric, rv in raw[key].items():
            vv = view[key][metric]
            ok, rel = close(rv, vv, rel_tol, abs_tol)
            if rel != math.inf:
                res.max_rel = max(res.max_rel, rel)
            if not ok:
                res.mismatches.append((key, metric, rv, vv))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", help="substring filter on case id")
    ap.add_argument("--rel-tol", type=float, default=1e-6)
    ap.add_argument("--abs-tol", type=float, default=1e-3)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    client = get_clickhouse_client(timeout=args.timeout)
    client.settings = {**(client.settings or {}), "max_execution_time": args.timeout}
    cases = [c for c in build_matrix() if not args.filter or args.filter in c.id]

    results: list[Result] = []
    hdr = f"{'case':<48} {'raw_ms':>9} {'view_ms':>8} {'raw_n':>6} {'view_n':>6}"
    print(hdr + f" {'miss_v':>6} {'miss_r':>6} {'bad':>5} {'max_rel':>9}  status")
    for case in cases:
        r = compare(case, client, args.rel_tol, args.abs_tol)
        results.append(r)
        if r.error == "raw-only path":
            status = "SKIP raw-only"
        else:
            status = "OK" if r.ok else ("ERROR " + (r.error or "") if r.error else "DIFF")
        print(
            f"{r.case.id:<48} {r.raw_ms:>9.0f} {r.view_ms:>8.0f} {r.raw_rows:>6} {r.view_rows:>6} "
            f"{r.missing_in_view:>6} {r.missing_in_raw:>6} {len(r.mismatches):>5} {r.max_rel:>9.2e}  {status}",
            flush=True,
        )
        for key, metric, rv, vv in r.mismatches[:5]:
            print(f"    {key} {metric}: raw={rv} view={vv}")

    bad = [r for r in results if not r.ok and r.error != "raw-only path"]
    slow = [r for r in results if r.view_ms > 100]
    print(f"\n{len(results)} cases, {len(bad)} failing, {len(slow)} view queries over 100ms")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
