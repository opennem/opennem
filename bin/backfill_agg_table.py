# ruff: noqa: E501
"""Apply migration 0006 and backfill fueltech_region_intervals from unit_intervals FINAL (#763). DEV ONLY.

Usage: PYTHONPATH=$PWD uv run --no-sync python bin/backfill_agg_table.py [--days 90] [--migrate] [--sleep 3]

Aborts unless the resolved clickhouse host contains `ch-dev`. Never prints credentials. Only creates
the new table (via the migration runner) and writes to it; unit_intervals and every other table are
only read. One day per query, sequential, with a pause between days (shared dev box).
"""

import argparse
import sys
from datetime import UTC, datetime, timedelta

from opennem import settings
from opennem.aggregates.fueltech_region_intervals import rebuild_range_sync
from opennem.db.clickhouse.client import get_clickhouse_client


def assert_dev() -> None:
    host = settings.clickhouse_url.host or ""
    if "ch-dev" not in host:
        sys.exit(f"refusing to write: clickhouse host {host!r} is not ch-dev")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--sleep", type=float, default=3.0)
    ap.add_argument("--migrate", action="store_true", help="apply pending clickhouse migrations first (0006 creates the table)")
    args = ap.parse_args()
    assert_dev()
    client = get_clickhouse_client(timeout=900)
    if args.migrate:
        from opennem.db.clickhouse.migrations import MigrationRunner

        runner = MigrationRunner(client)
        print("pending:", [m.name for m in runner.pending()])
        print("applied:", runner.up())
    end = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=10)
    end = end.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    start = end - timedelta(days=args.days + 1)
    rows = rebuild_range_sync(start, end, chunk_days=1, sleep_s=args.sleep, client=client)
    print(f"backfilled {start:%Y-%m-%d} to {end:%Y-%m-%d}: {rows} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
