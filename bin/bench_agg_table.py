# ruff: noqa: C408, E501
"""Read-only before/after clickhouse benchmark for fueltech_region_intervals routing (#763).

Usage: PYTHONPATH=$PWD uv run --no-sync python bin/bench_agg_table.py [shape ...]

Runs each tracker shape n times unrouted (unit_intervals FINAL) and routed, one query at a time, and
reports first-run and median read_rows / duration / memory from system.query_log. SELECTs only.
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
    "7d1h_NSW1_pow": (timedelta(days=7), Interval.HOUR, "NSW1", ["power"]),
    "30d30m_NSW1_pow": (timedelta(days=30), Interval.HALF_HOUR, "NSW1", ["power"]),
    "30d30m_NEM_pow": (timedelta(days=30), Interval.HALF_HOUR, None, ["power"]),
}


def build(shape: str, end: datetime, route: bool) -> tuple[str, dict]:
    span, interval, region, metrics = SHAPES[shape]
    pg = PrimaryGrouping.NETWORK_REGION if region else PrimaryGrouping.NETWORK
    sql, params, _ = get_timeseries_query(
        query_type=QueryType.DATA, network=get_api_network_from_code("NEM"), metrics=[Metric(m) for m in metrics],
        interval=interval, date_start=end - span, date_end=end, primary_grouping=pg,
        secondary_groupings=[SecondaryGrouping.FUELTECH], network_region=region, columnar=True,
        use_agg_table=route, use_subday_mv=False,
    )  # fmt: skip
    return sql, params


def timed(client, sql: str, params: dict, n: int = 5) -> dict:  # noqa: ANN001
    ids = []
    for _ in range(n):
        qid = str(uuid.uuid4())
        client.execute(sql, params, query_id=qid)
        ids.append(qid)
        time.sleep(0.5)
    client.execute("SYSTEM FLUSH LOGS")
    rows = [
        client.execute(
            "SELECT read_rows, query_duration_ms, memory_usage FROM system.query_log WHERE query_id = %(q)s AND type = 'QueryFinish'",
            {"q": q},
        )[0]
        for q in ids
    ]
    return {
        "read_rows": statistics.median(r[0] for r in rows),
        "first_ms": rows[0][1],
        "median_ms": statistics.median(r[1] for r in rows),
        "mem_mb": round(statistics.median(r[2] for r in rows) / 1e6, 1),
    }


def main() -> None:
    client = get_clickhouse_client(timeout=300)
    now = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=10)
    end = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    for shape in sys.argv[1:] or list(SHAPES):
        for route in (False, True):
            sql, params = build(shape, end, route)
            print(shape, "agg" if route else "raw", timed(client, sql, params), flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
