# ruff: noqa: E501
"""Read-only per-day sweep: fueltech_region_intervals vs unit_intervals FINAL aggregates (#763).

Usage: PYTHONPATH=$PWD uv run --no-sync python bin/sweep_agg_table.py [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--sleep 2]

Default range: every day from the table's first interval to the later of its last interval and the
last unit_intervals day. Days present in only one side are reported. SELECTs only (safe on any
environment, but point it at dev unless you mean otherwise). Exit 1 on any mismatching day.
"""

import argparse
import sys
import time
from datetime import date, timedelta
from typing import cast

from opennem.aggregates.fueltech_region_intervals import AGG_TABLE, compare_day
from opennem.db.clickhouse.client import get_clickhouse_client


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--sleep", type=float, default=2.0)
    args = ap.parse_args()
    client = get_clickhouse_client(timeout=600)
    lo, hi = cast(
        "list[tuple[date | None, date | None]]",
        client.execute(f"SELECT toDate(min(interval)), toDate(max(interval)) FROM {AGG_TABLE}"),
    )[0]
    if lo is None or hi is None:
        print("table is empty")
        return 1
    raw_hi = cast(
        "list[tuple[date | None]]",
        client.execute("SELECT toDate(max(interval)) FROM unit_intervals WHERE interval > now() - INTERVAL 3 DAY"),
    )[0][0]
    first = date.fromisoformat(args.start) if args.start else lo
    last = date.fromisoformat(args.end) if args.end else max(hi, raw_hi or hi)
    bad = days = 0
    day = first
    while day <= last:
        mism = compare_day(client, day)
        days += 1
        if mism:
            bad += 1
            print(f"DIFF {day} {'; '.join(mism)}", flush=True)
        day += timedelta(days=1)
        time.sleep(args.sleep)
    print(f"sweep {first} to {last}: {days} days, {bad} mismatching")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
