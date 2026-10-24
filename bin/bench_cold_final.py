# ruff: noqa: C408, E501
"""Read-only cold-path ClickHouse benchmark for tracker shapes (#761).

Usage: PYTHONPATH=$PWD uv run --no-sync python bin/bench_cold_final.py [variant,...] [shape ...]

Runs `get_timeseries_query(columnar=True)` per shape n times, with optional per-query settings or a
FINAL-less lower bound, and reports medians of read_rows / read_bytes / server duration / memory from
system.query_log. SELECTs only. One query at a time (shared dev box).
"""

import statistics
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta

from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.db.clickhouse.client import get_clickhouse_client

ALL4 = ["power", "energy", "emissions", "market_value"]
SHAPES: dict[str, tuple[timedelta, Interval, str | None, list[str]]] = {
    "1d5m_NSW1_pow": (timedelta(days=1), Interval.INTERVAL, "NSW1", ["power"]),
    "3d5m_NSW1_pow": (timedelta(days=3), Interval.INTERVAL, "NSW1", ["power"]),
    "7d5m_NSW1_pow": (timedelta(days=7), Interval.INTERVAL, "NSW1", ["power"]),
    "7d5m_NEM_pow": (timedelta(days=7), Interval.INTERVAL, None, ["power"]),
    "7d5m_NSW1_4m": (timedelta(days=7), Interval.INTERVAL, "NSW1", ALL4),
    "30d30m_NSW1_pow": (timedelta(days=30), Interval.HALF_HOUR, "NSW1", ["power"]),
    "30d30m_NEM_pow": (timedelta(days=30), Interval.HALF_HOUR, None, ["power"]),
}
# name -> (query settings, replace FINAL with plain table: a lower bound, NOT equivalent)
VARIANTS: dict[str, tuple[dict[str, int], bool]] = {
    "base": ({}, False),
    "nofinal_lower_bound": ({}, True),
    "dnm": ({"do_not_merge_across_partitions_select_final": 1}, False),
    "threads8": ({"max_threads": 8}, False),
    "threads2": ({"max_threads": 2}, False),
    "no_read_in_order": ({"optimize_read_in_order": 0}, False),
    "no_layers": ({"split_intersecting_parts_ranges_into_layers_final": 0}, False),
    "block131k": ({"max_block_size": 131072}, False),
}


def build(shape: str, end: datetime) -> tuple[str, dict]:
    span, interval, region, metrics = SHAPES[shape]
    pg = PrimaryGrouping.NETWORK_REGION if region else PrimaryGrouping.NETWORK
    sql, params, _ = get_timeseries_query(
        query_type=QueryType.DATA, network=get_api_network_from_code("NEM"), metrics=[Metric(m) for m in metrics],
        interval=interval, date_start=end - span, date_end=end, primary_grouping=pg,
        secondary_groupings=[SecondaryGrouping.FUELTECH], network_region=region, columnar=True,
    )  # fmt: skip
    return sql, params


def timed(client, sql: str, params: dict, settings: dict[str, int], n: int = 5) -> dict:  # noqa: ANN001
    ids = []
    for _ in range(n):
        qid = str(uuid.uuid4())
        client.execute(sql, params, query_id=qid, settings=settings)
        ids.append(qid)
        time.sleep(0.5)
    client.execute("SYSTEM FLUSH LOGS")
    rows = [
        client.execute(
            "SELECT read_rows, read_bytes, query_duration_ms, memory_usage FROM system.query_log WHERE query_id = %(q)s AND type = 'QueryFinish'",
            {"q": q},
        )[0]
        for q in ids
    ]
    med = [statistics.median(r[i] for r in rows) for i in range(4)]
    return {"read_rows": med[0], "read_mb": round(med[1] / 1e6, 1), "ms": med[2], "mem_mb": round(med[3] / 1e6, 1)}


def main() -> None:
    client = get_clickhouse_client(timeout=300)
    now = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=10)
    end = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    variants = (sys.argv[1] if len(sys.argv) > 1 else "base").split(",")
    for v in variants:
        settings, nofinal = VARIANTS[v]
        for shape in sys.argv[2:] or list(SHAPES):
            sql, params = build(shape, end)
            if nofinal:
                sql = sql.replace("unit_intervals FINAL", "unit_intervals")
            print(v, shape, timed(client, sql, params, settings), flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
