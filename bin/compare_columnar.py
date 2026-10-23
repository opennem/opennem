# ruff: noqa: C408
"""Compare the columnar timeseries path with the row path against a real ClickHouse (#740).

Read-only SELECTs. Usage: PYTHONPATH=$PWD uv run --no-sync python bin/compare_columnar.py [--quick]
Asserts JSON equality and byte equality (orjson) per call, prints python cpu / ch time per path.
"""

import sys
import time
from datetime import UTC, datetime, timedelta

import orjson

from opennem.api.queries import QueryType, columnar_supported, get_timeseries_query
from opennem.api.timeseries import columnar_to_timeseries_response, rows_to_timeseries_response
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse.client import get_clickhouse_client

REGIONS = ["NSW1", "VIC1", "TAS1", None]
WINDOWS = {"1d": (timedelta(days=1), Interval.INTERVAL), "3d": (timedelta(days=3), Interval.INTERVAL),
           "7d": (timedelta(days=7), Interval.INTERVAL), "30d": (timedelta(days=30), Interval.HALF_HOUR)}  # fmt: skip
CALLS = [
    ("data", "power", ["power"]), ("data", "emissions_intensity", ["emissions", "power"]),
    ("data", "market_value", ["market_value"]), ("data", "emissions", ["emissions"]),
    ("market", "price", ["price"]), ("market", "demand", ["demand"]),
    ("market", "renewables", ["generation_renewable", "demand_gross"]),
    ("market", "curtailment", ["curtailment_solar_utility", "curtailment_wind"]),
    ("market", "renewable_share", ["renewable_proportion"]), ("market", "flows", ["flow_imports", "flow_exports"]),
]  # fmt: skip
EXTRA = [("data", "power_fueltech_group", ["power"], SecondaryGrouping.FUELTECH_GROUP),
         ("data", "power_nosec", ["power"], None)]  # fmt: skip


def run(client, kind, metrics, region, span, interval, sec, now):  # noqa: ANN001
    net = get_api_network_from_code("NEM")
    qt = QueryType.DATA if kind == "data" else QueryType.MARKET
    pg = PrimaryGrouping.NETWORK_REGION if region else PrimaryGrouping.NETWORK
    ms = [Metric(m) for m in metrics]
    secs = [sec] if sec else None
    kw = dict(query_type=qt, network=net, metrics=ms, interval=interval, date_start=now - span, date_end=now,
              primary_grouping=pg, secondary_groupings=secs, network_region=region)  # fmt: skip
    fk = dict(network="NEM", metrics=ms, interval=interval, primary_grouping=pg, secondary_groupings=secs)
    assert columnar_supported(qt, pg, secs)
    q0, p0, c0 = get_timeseries_query(**kw)
    q1, p1, c1 = get_timeseries_query(**kw, columnar=True)
    t = time.perf_counter()
    r0 = client.execute(q0, p0)
    ch0 = time.perf_counter() - t
    t = time.perf_counter()
    r1 = client.execute(q1, p1)
    ch1 = time.perf_counter() - t
    t = time.process_time()
    o0 = rows_to_timeseries_response(c0, r0, **fk)
    py0 = time.process_time() - t
    t = time.process_time()
    o1 = columnar_to_timeseries_response(c1, r1, **fk)
    py1 = time.process_time() - t
    for o in (o0, o1):
        o["created_at"] = o["version"] = ""
    b0, b1 = orjson.dumps(o0), orjson.dumps(o1)
    return len(r0), len(r1), ch0, ch1, py0, py1, b0 == b1, o0, o1


def first_diff(a, b, path=""):  # noqa: ANN001
    if type(a) is not type(b) and not (isinstance(a, list | tuple) and isinstance(b, list | tuple)):
        return f"{path}: type {type(a)} vs {type(b)}"
    if isinstance(a, dict):
        if list(a) != list(b):
            return f"{path}: keys {list(a)[:6]} vs {list(b)[:6]}"
        for k in a:
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
    elif isinstance(a, list | tuple):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
    elif a != b:
        return f"{path}: {a!r} vs {b!r}"
    return None


def main() -> int:
    quick = "--quick" in sys.argv
    client = get_clickhouse_client(timeout=120)
    now = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=10)
    now = now.replace(minute=now.minute - now.minute % 30, second=0, microsecond=0) - timedelta(hours=1)
    fails = 0
    tot = [0.0] * 4
    n = 0
    calls = [(k, nm, m, None) for k, nm, m in CALLS] + ([] if quick else EXTRA)
    for kind, name, metrics, sec in calls:
        for wname, (span, interval) in WINDOWS.items():
            for region in REGIONS[:1] if quick else REGIONS:
                s = sec if sec is not None or kind != "data" else SecondaryGrouping.FUELTECH
                if name == "power_nosec":
                    s = None
                try:
                    r0, r1, ch0, ch1, py0, py1, same, o0, o1 = run(client, kind, metrics, region, span, interval, s, now)
                except Exception as e:  # noqa: BLE001
                    print(f"ERROR {kind}/{name}/{wname}/{region}: {str(e)[:300]}")
                    fails += 1
                    continue
                d = first_diff(o0, o1)
                ok = same and d is None
                fails += not ok
                n += 1
                tot = [tot[0] + ch0, tot[1] + ch1, tot[2] + py0, tot[3] + py1]
                print(f"{'OK  ' if ok else 'FAIL'} {kind}/{name} {wname} {region or 'NEM'} rows {r0}->{r1}series "
                      f"ch {ch0 * 1000:.0f}->{ch1 * 1000:.0f}ms py {py0 * 1000:.0f}->{py1 * 1000:.0f}ms"
                      f"{'' if ok else ' DIFF ' + str(d)}")  # fmt: skip
    print(f"\n{n} compared, {fails} failed. totals ch {tot[0]:.1f}->{tot[1]:.1f}s py {tot[2]:.1f}->{tot[3]:.1f}s")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
