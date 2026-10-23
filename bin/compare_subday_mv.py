# ruff: noqa: C408, E501
"""Prove sub-day routing to fueltech_intervals_mv equals unit_intervals FINAL (#742).

Read-only SELECTs against the clickhouse in settings (dev). Usage:
  PYTHONPATH=$PWD uv run --no-sync python bin/compare_subday_mv.py [--quick] [--unguarded] [--sweep YYYY-MM YYYY-MM]

Matrix mode runs each shape through get_timeseries_query(columnar=True, use_subday_mv=False|True),
the SAME columnar assembly, and asserts identical orjson bytes. Sweep mode joins the raw FINAL
aggregation to the view FINAL per (interval, network, region, fueltech) month by month and counts
rows that are missing or differ.
"""

import sys
import time
from datetime import UTC, date, datetime, timedelta

import orjson

from opennem.api.queries import QueryType, get_timeseries_query, subday_mv_supported
from opennem.api.timeseries import columnar_to_timeseries_response
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse.client import get_clickhouse_client

REGIONS = {"NEM": ["NSW1", "QLD1", "SA1", "TAS1", "VIC1", None], "WEM": ["WEM", None], "AU": [None]}
WINDOWS = {"1d": (timedelta(days=1), Interval.INTERVAL), "3d": (timedelta(days=3), Interval.INTERVAL),
           "7d": (timedelta(days=7), Interval.INTERVAL), "30d": (timedelta(days=30), Interval.HALF_HOUR),
           "7d1h": (timedelta(days=7), Interval.HOUR)}  # fmt: skip
METRIC_SETS = [["power", "energy", "emissions", "market_value"], ["emissions", "power"], ["power"]]
SECS = [SecondaryGrouping.FUELTECH, SecondaryGrouping.FUELTECH_GROUP, None]


def run(client, net, region, metrics, sec, span, interval, end, route):  # noqa: ANN001
    network = get_api_network_from_code(net)
    pg = PrimaryGrouping.NETWORK_REGION if region else PrimaryGrouping.NETWORK
    ms = [Metric(m) for m in metrics]
    secs = [sec] if sec else None
    kw = dict(query_type=QueryType.DATA, network=network, metrics=ms, interval=interval, date_start=end - span,
              date_end=end, primary_grouping=pg, secondary_groupings=secs, network_region=region)  # fmt: skip
    q, p, cols = get_timeseries_query(**kw, columnar=True, use_subday_mv=route)
    assert (" fueltech_intervals_mv FINAL" in q) == route, "routing not applied as requested"
    t = time.perf_counter()
    rows = client.execute(q, p)
    dt = time.perf_counter() - t
    out = columnar_to_timeseries_response(cols, rows, network=net, metrics=ms, interval=interval, primary_grouping=pg,
                                          secondary_groupings=secs)  # fmt: skip
    out["created_at"] = out["version"] = ""
    return orjson.dumps(out), len(rows), dt, out


def matrix(client, quick: bool) -> int:  # noqa: ANN001
    now = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=10)
    now = now.replace(minute=0, second=0, microsecond=0)
    day0 = now.replace(hour=0)
    # (end, windows) anchors: live edge, every day end in the last 14 days (1d), mid-range, and old windows
    anchors = [(now - timedelta(hours=1), list(WINDOWS)), (now - timedelta(hours=1, minutes=30), ["1d"])]
    anchors += [(day0 - timedelta(days=i), ["1d", "3d"] if i % 3 == 0 else ["1d"]) for i in range(0, 14)]
    anchors += [(day0 - timedelta(days=d), ["7d", "30d", "7d1h"]) for d in (5, 9, 16, 23, 30, 37)]
    anchors += [(datetime(*a), ["1d", "7d", "30d"]) for a in
                [(2026, 6, 15), (2025, 12, 1), (2024, 7, 1), (2023, 9, 24), (2021, 1, 1), (2015, 3, 1), (2009, 3, 8)]]  # fmt: skip
    if quick:
        anchors = anchors[:3]
    n = fails = noise = skipped = 0
    t_old = t_new = 0.0
    for end, wnames in anchors:
        for wname in wnames:
            span, interval = WINDOWS[wname]
            for net, regions in REGIONS.items():
                for region in regions:
                    for sec in SECS:
                        for metrics in METRIC_SETS[: 1 if wname.startswith("30") else None]:
                            if not subday_mv_supported(QueryType.DATA, interval, [Metric(m) for m in metrics],
                                                       [sec] if sec else None, date_start=end - span):  # fmt: skip
                                skipped += 1  # falls back to the raw table in production, nothing to compare
                                continue
                            tag = f"{end:%Y-%m-%d %H:%M} {wname} {net}/{region or 'ALL'} {sec or 'nosec'} {'+'.join(metrics)}"
                            try:
                                b0, r0, d0, o0 = run(client, net, region, metrics, sec, span, interval, end, False)
                                b1, r1, d1, o1 = run(client, net, region, metrics, sec, span, interval, end, True)
                            except Exception as e:  # noqa: BLE001
                                print(f"ERROR {tag}: {str(e)[:200]}", flush=True)
                                fails += 1
                                continue
                            n += 1
                            t_old, t_new = t_old + d0, t_new + d1
                            if b0 != b1:
                                if first_diff(o0, o1, tol=1.5e-6) is None:
                                    noise += 1  # same to float summation order at the 6th decimal
                                    continue
                                fails += 1
                                print(f"DIFF {tag} series {r0} vs {r1}: {first_diff(o0, o1)}", flush=True)
    print(
        f"matrix: {n} compared, {n - fails - noise} byte-identical, {noise} 1e-6 float noise only, {fails} real diffs/errors, {skipped} not routed (age guard), ch {t_old:.1f}s -> {t_new:.1f}s",
        flush=True,
    )
    return fails


def first_diff(a, b, path="", tol=0.0):  # noqa: ANN001
    """First mismatch; numbers within `tol` (abs) count as equal, None vs number never does."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            d = first_diff(a[k], b.get(k), f"{path}.{k}", tol)
            if d:
                return d
    elif isinstance(a, list | tuple) and isinstance(b, list | tuple):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            d = first_diff(x, y, f"{path}[{i}]", tol)
            if d:
                return d
    elif isinstance(a, float) and isinstance(b, float) and abs(a - b) <= tol:
        return None
    elif a != b:
        return f"{path}: {a!r} vs {b!r}"
    return None


SWEEP_SQL = """
SELECT
    count() AS n,
    countIf(r.inr = 0) AS only_mv,
    countIf(m.inm = 0) AS only_raw,
    countIf(NOT (isNull(r.generated) = isNull(m.generated) AND ifNull(abs(r.generated - m.generated), 0) <= 1e-6)) AS d_gen,
    countIf(NOT (isNull(r.energy) = isNull(m.energy) AND ifNull(abs(r.energy - m.energy), 0) <= 1e-6)) AS d_energy,
    countIf(NOT (isNull(r.emissions) = isNull(m.emissions) AND ifNull(abs(r.emissions - m.emissions), 0) <= 1e-6)) AS d_em,
    countIf(NOT (isNull(r.market_value) = isNull(m.market_value) AND ifNull(abs(r.market_value - m.market_value), 0) <= 1e-6)) AS d_mv,
    anyIf(tuple(r.interval, r.network_id, r.network_region, r.fueltech_id), NOT (isNull(r.generated) = isNull(m.generated)
        AND ifNull(abs(r.generated - m.generated), 0) <= 1e-6)) AS first_bad
FROM (
    SELECT 1 AS inr, interval, network_id, network_region, fueltech_id, fueltech_group_id, sum(generated) AS generated, sum(energy) AS energy,
           sum(emissions) AS emissions, sum(market_value) AS market_value
    FROM unit_intervals FINAL WHERE interval >= %(s)s AND interval < %(e)s
    GROUP BY interval, network_id, network_region, fueltech_id, fueltech_group_id) AS r
FULL OUTER JOIN (
    SELECT 1 AS inm, interval, network_id, network_region, fueltech_id, fueltech_group_id, generated, energy, emissions, market_value
    FROM fueltech_intervals_mv FINAL WHERE interval >= %(s)s AND interval < %(e)s) AS m
USING (interval, network_id, network_region, fueltech_id, fueltech_group_id)
"""


def sweep(client, first: str, last: str) -> int:  # noqa: ANN001
    y, m = map(int, first.split("-"))
    ly, lm = map(int, last.split("-"))
    bad = 0
    while (y, m) <= (ly, lm):
        s = date(y, m, 1)
        e = date(y + (m == 12), m % 12 + 1, 1)
        # one-sided join rows (present on one side only) show up as generated/energy null mismatch; count them via sides
        row = client.execute(SWEEP_SQL.replace("USING (", "USING (").replace("FULL OUTER JOIN", "FULL OUTER JOIN"),
                             {"s": s, "e": e})[0]  # fmt: skip
        flag = "OK  " if row[1:7] == (0, 0, 0, 0, 0, 0) else "DIFF"
        bad += flag == "DIFF"
        print(
            f"{flag} {s:%Y-%m} rows {row[0]} only_mv {row[1]} only_raw {row[2]} d_gen {row[3]} d_energy {row[4]} d_em {row[5]} d_mv {row[6]} first {row[7]}",
            flush=True,
        )
        y, m = (y + (m == 12), m % 12 + 1)
    print(f"sweep: {bad} months with diffs")
    return bad


def main() -> int:
    if "--unguarded" in sys.argv:  # informational: ignore the age guard to see historical view drift
        from opennem import settings

        settings.clickhouse_subday_mv_max_age_days = 100_000
    client = get_clickhouse_client(timeout=300)
    if "--sweep" in sys.argv:
        i = sys.argv.index("--sweep")
        return 1 if sweep(client, sys.argv[i + 1], sys.argv[i + 2]) else 0
    return 1 if matrix(client, "--quick" in sys.argv) else 0


if __name__ == "__main__":
    sys.exit(main())
