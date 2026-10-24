# ruff: noqa: C408, E501
"""Prove routing to fueltech_region_intervals equals unit_intervals FINAL, byte for byte (#763).

Read-only SELECTs against the clickhouse in settings (dev). Usage:
  PYTHONPATH=$PWD uv run --no-sync python bin/compare_agg_table.py [--quick] [--sleep 0.2] [--log-id PREFIX]

Each shape runs through get_timeseries_query(columnar=True, use_agg_table=False|True), the SAME
columnar assembly, and the orjson bytes of the response must be identical. Query ids carry a prefix so
system.query_log read_rows / duration can be summed per variant afterwards (--stats).
"""

import argparse
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta

import orjson

from opennem.api.queries import AGG_TABLE, QueryType, agg_table_supported, get_timeseries_query
from opennem.api.timeseries import columnar_to_timeseries_response
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse.client import get_clickhouse_client

REGIONS = ["NSW1", "QLD1", "SA1", "TAS1", "VIC1", None]
WINDOWS = {"1d": (timedelta(days=1), Interval.INTERVAL), "3d": (timedelta(days=3), Interval.INTERVAL),
           "7d": (timedelta(days=7), Interval.INTERVAL), "30d": (timedelta(days=30), Interval.HALF_HOUR),
           "7d1h": (timedelta(days=7), Interval.HOUR)}  # fmt: skip
METRIC_SETS = [["power"], ["emissions", "power"], ["market_value"], ["energy", "emissions"]]
SECS = [SecondaryGrouping.FUELTECH, SecondaryGrouping.FUELTECH_GROUP, None]


def run(client, region, metrics, sec, span, interval, end, route, prefix):  # noqa: ANN001
    network = get_api_network_from_code("NEM")
    pg = PrimaryGrouping.NETWORK_REGION if region else PrimaryGrouping.NETWORK
    ms = [Metric(m) for m in metrics]
    secs = [sec] if sec else None
    kw = dict(query_type=QueryType.DATA, network=network, metrics=ms, interval=interval, date_start=end - span,
              date_end=end, primary_grouping=pg, secondary_groupings=secs, network_region=region)  # fmt: skip
    q, p, cols = get_timeseries_query(**kw, columnar=True, use_agg_table=route, use_subday_mv=False)
    assert (f" {AGG_TABLE} FINAL" in q) == route, "routing not applied as requested"
    qid = f"{prefix}-{'agg' if route else 'raw'}-{uuid.uuid4().hex[:8]}"
    t = time.perf_counter()
    rows = client.execute(q, p, query_id=qid)
    dt = time.perf_counter() - t
    out = columnar_to_timeseries_response(cols, rows, network="NEM", metrics=ms, interval=interval, primary_grouping=pg,
                                          secondary_groupings=secs)  # fmt: skip
    out["created_at"] = out["version"] = ""
    return orjson.dumps(out), len(rows), dt, out


def first_diff(a, b, path=""):  # noqa: ANN001
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            d = first_diff(a[k], b.get(k), f"{path}.{k}")
            if d:
                return d
    elif isinstance(a, list | tuple) and isinstance(b, list | tuple):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
    elif a != b:
        return f"{path}: {a!r} vs {b!r}"
    return None


def anchors(quick: bool):  # noqa: ANN201
    now = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=10)
    now = now.replace(minute=0, second=0, microsecond=0)
    day0 = now.replace(hour=0)
    a = [(now - timedelta(hours=1), ["1d", "3d", "7d", "7d1h"]), (now - timedelta(hours=1, minutes=30), ["1d"])]
    a += [(day0 - timedelta(days=i), ["1d", "3d"] if i % 3 == 0 else ["1d"]) for i in range(0, 14)]
    a += [(day0 - timedelta(days=d), ["7d", "7d1h"]) for d in (1, 4, 8, 12)]
    a += [(day0 - timedelta(days=d), ["30d"]) for d in (0, 3, 9, 13)]
    return a[:3] if quick else a


def matrix(client, quick: bool, sleep: float, prefix: str) -> int:  # noqa: ANN001
    n = fails = skipped = 0
    t_old = t_new = 0.0
    for end, wnames in anchors(quick):
        for wname in wnames:
            span, interval = WINDOWS[wname]
            for region in REGIONS:
                for sec in SECS:
                    for metrics in METRIC_SETS[: 1 if wname.startswith("30") else None]:
                        pg = PrimaryGrouping.NETWORK_REGION if region else PrimaryGrouping.NETWORK
                        if not agg_table_supported(QueryType.DATA, pg, interval, [Metric(m) for m in metrics],
                                                   [sec] if sec else None, date_start=end - span):  # fmt: skip
                            skipped += 1
                            continue
                        tag = f"{end:%Y-%m-%d %H:%M} {wname} NEM/{region or 'ALL'} {sec or 'nosec'} {'+'.join(metrics)}"
                        try:
                            b0, r0, d0, o0 = run(client, region, metrics, sec, span, interval, end, False, prefix)
                            b1, r1, d1, o1 = run(client, region, metrics, sec, span, interval, end, True, prefix)
                        except Exception as e:  # noqa: BLE001
                            print(f"ERROR {tag}: {str(e)[:200]}", flush=True)
                            fails += 1
                            continue
                        n += 1
                        t_old, t_new = t_old + d0, t_new + d1
                        if b0 != b1:
                            fails += 1
                            print(f"DIFF {tag} series {r0} vs {r1}: {first_diff(o0, o1)}", flush=True)
                        time.sleep(sleep)
    print(f"matrix: {n} compared, {n - fails} byte-identical, {fails} diffs/errors, {skipped} not routed (guard), "
          f"client wall {t_old:.1f}s raw -> {t_new:.1f}s agg", flush=True)  # fmt: skip
    return fails


def stats(client, prefix: str) -> None:  # noqa: ANN001
    client.execute("SYSTEM FLUSH LOGS")
    rows = client.execute(
        """
        SELECT if(position(query_id, '-agg-') > 0, 'agg', 'raw') AS v, count(), round(avg(query_duration_ms), 1),
               round(quantile(0.5)(query_duration_ms), 1), round(quantile(0.95)(query_duration_ms), 1),
               round(avg(read_rows)), round(quantile(0.5)(read_rows)), round(avg(memory_usage) / 1e6, 1)
        FROM system.query_log WHERE type = 'QueryFinish' AND startsWith(query_id, %(p)s) GROUP BY v ORDER BY v
        """,
        {"p": prefix + "-"},
    )
    print("variant n avg_ms p50_ms p95_ms avg_read_rows p50_read_rows avg_mem_mb")
    for r in rows:
        print(*r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.2)
    ap.add_argument("--prefix", default=f"agg763-{uuid.uuid4().hex[:6]}")
    ap.add_argument("--stats", action="store_true", help="only print query_log stats for --prefix")
    args = ap.parse_args()
    client = get_clickhouse_client(timeout=300)
    if args.stats:
        stats(client, args.prefix)
        return 0
    print("prefix", args.prefix)
    bad = matrix(client, args.quick, args.sleep, args.prefix)
    stats(client, args.prefix)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
