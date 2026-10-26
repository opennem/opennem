"""
fueltech_region_intervals: additive per (interval, network, region, fueltech) sums (#763).

Written from the SAME prepared rows (same dataframe, same `version`) that write `unit_intervals`,
so it cannot diverge by construction; not a materialized view, so a partial re-insert cannot
replace a full row with a partial sum (#755). Stores exactly the sums of what unit_intervals
stores: no energy recompute (#746).

Safety rules:
- every write here is flag-gated (`CLICKHOUSE_AGG_TABLE_WRITE`) and failure-isolated: a failure
  is logged + sent to sentry and NEVER propagates into the unit_intervals write path.
- `rebuild_range` inserts the recomputed rows first (new version) and then deletes older rows in
  the range, so readers never see a gap; stale keys that no longer exist are removed.
"""

import asyncio
import logging
import time
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import polars as pl
import sentry_sdk

from opennem import settings
from opennem.db.clickhouse import get_clickhouse_client, insert_async

logger = logging.getLogger("opennem.aggregates.fueltech_region_intervals")

AGG_TABLE = "fueltech_region_intervals"

KEY_COLS = ["interval", "network_id", "network_region", "fueltech_id", "fueltech_group_id"]
SUM_COLS = ["generated", "energy", "emissions", "market_value"]

INSERT_SQL = f"""
INSERT INTO {AGG_TABLE}
(interval, network_id, network_region, fueltech_id, fueltech_group_id,
 generated, energy, emissions, market_value, unit_count, version)
VALUES
"""

# positions in the unit_intervals insert tuple (see `_prepare_unit_interval_data`)
_UI_POS = {
    "interval": 0,
    "network_id": 1,
    "network_region": 2,
    "fueltech_id": 6,
    "fueltech_group_id": 7,
    "generated": 9,
    "energy": 10,
    "emissions": 12,
    "market_value": 14,
    "version": 15,
}

_REBUILD_INSERT_SQL = f"""
INSERT INTO {AGG_TABLE}
SELECT
    interval, network_id, network_region, fueltech_id, fueltech_group_id,
    sum(generated), sum(energy), sum(emissions), sum(market_value),
    toUInt32(count()), toUInt64(%(version)s)
FROM unit_intervals FINAL
WHERE interval >= %(start)s AND interval < %(end)s
GROUP BY interval, network_id, network_region, fueltech_id, fueltech_group_id
"""

_REBUILD_DELETE_SQL = f"""
ALTER TABLE {AGG_TABLE} DELETE
WHERE interval >= %(start)s AND interval < %(end)s AND version < %(version)s
"""


def aggregate_rows(prepared: Sequence[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    """Collapse prepared unit_intervals rows to one row per (interval, network, region, fueltech).

    A sum over only-NULL inputs stays NULL (as clickhouse `sum(Nullable)` does), otherwise sums are
    rounded to the 4dp unit_intervals already holds. `version` is the batch's version.
    """
    if not prepared:
        return []
    cols = {name: [r[i] for r in prepared] for name, i in _UI_POS.items()}
    schema: dict[str, Any] = dict.fromkeys(SUM_COLS, pl.Float64)
    schema.update(dict.fromkeys(KEY_COLS[1:], pl.String))
    schema.update({"interval": pl.Datetime("ms"), "version": pl.UInt64})
    df = pl.DataFrame(cols, schema=schema)
    agg = (
        df.group_by(KEY_COLS)
        .agg(
            *[pl.when(pl.col(c).count() > 0).then(pl.col(c).sum()).otherwise(None).round(4).alias(c) for c in SUM_COLS],
            pl.len().cast(pl.UInt32).alias("unit_count"),
            pl.col("version").max().alias("version"),
        )
        .sort(KEY_COLS)
    )
    return agg.select([*KEY_COLS, *SUM_COLS, "unit_count", "version"]).rows()


def _report_failure(what: str, exc: BaseException) -> None:
    logger.error(f"fueltech_region_intervals {what} failed (unit_intervals unaffected): {exc!r}")
    try:
        with sentry_sdk.new_scope() as scope:
            scope.fingerprint = ["fueltech-region-intervals-failure", what]
            scope.set_tag("agg_table", AGG_TABLE)
            sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001 - reporting must never raise either
        logger.exception("sentry capture failed")


async def write_aggregate(prepared: Sequence[tuple[Any, ...]]) -> int:
    """Write the aggregate rows for rows just inserted into unit_intervals. Never raises.

    No-op unless `CLICKHOUSE_AGG_TABLE_WRITE` is on. Returns rows written (0 on skip/failure).
    """
    if not settings.clickhouse_agg_table_write or not prepared:
        return 0
    try:
        rows = await asyncio.to_thread(aggregate_rows, prepared)
        await insert_async(INSERT_SQL, rows)
        return len(rows)
    except Exception as e:  # noqa: BLE001 - isolation is the point
        _report_failure("write", e)
        return 0


def rebuild_range_sync(
    start: datetime,
    end: datetime,
    *,
    chunk_days: int = 1,
    sleep_s: float = 0.0,
    client: Any = None,
    version: int | None = None,
) -> int:
    """Recompute the table over [start, end) from `unit_intervals FINAL`. Raises on failure.

    Per chunk: insert recomputed rows at a fresh version, then delete older rows in the chunk, so
    no reader sees a gap and keys that vanished from unit_intervals are dropped.
    Returns the number of rows in the table for the range afterwards.
    """
    client = client or get_clickhouse_client(timeout=600)
    version = version or int(time.time())
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=chunk_days), end)
        params = {"start": cur, "end": nxt, "version": version}
        client.execute(_REBUILD_INSERT_SQL, params)
        client.execute(_REBUILD_DELETE_SQL, params)
        logger.info(f"{AGG_TABLE}: rebuilt {cur} to {nxt}")
        cur = nxt
        if sleep_s and cur < end:
            time.sleep(sleep_s)
    res = client.execute(
        f"SELECT count() FROM {AGG_TABLE} FINAL WHERE interval >= %(start)s AND interval < %(end)s",
        {"start": start, "end": end},
    )
    return int(res[0][0])


async def rebuild_range(start: datetime, end: datetime, *, inclusive_end: bool = True) -> int:
    """Flag-gated, failure-isolated range rebuild for the repair entry points. Never raises.

    `end` is treated as inclusive of its 5 minute bucket by default (repair callers pass the last
    interval they wrote).
    """
    if not settings.clickhouse_agg_table_write:
        return 0
    try:
        stop = end + timedelta(minutes=5) if inclusive_end else end
        return await asyncio.to_thread(rebuild_range_sync, start, stop)
    except Exception as e:  # noqa: BLE001
        _report_failure("rebuild", e)
        return 0


# ---- comparison against unit_intervals FINAL (sweep script + worker check) ----

_COMPARE_COLS = ["n", "unit_count", *[f"{c}_nulls" for c in SUM_COLS], *[f"{c}_sum" for c in SUM_COLS]]

_AGG_DAY_SQL = f"""
SELECT
    count(), sum(unit_count),
    countIf(isNull(generated)), countIf(isNull(energy)), countIf(isNull(emissions)), countIf(isNull(market_value)),
    sum(generated), sum(energy), sum(emissions), sum(market_value)
FROM {AGG_TABLE} FINAL
WHERE interval >= %(start)s AND interval < %(end)s
"""

_RAW_DAY_SQL = """
SELECT
    count(), sum(unit_count),
    countIf(isNull(generated)), countIf(isNull(energy)), countIf(isNull(emissions)), countIf(isNull(market_value)),
    sum(generated), sum(energy), sum(emissions), sum(market_value)
FROM (
    SELECT sum(generated) AS generated, sum(energy) AS energy, sum(emissions) AS emissions,
           sum(market_value) AS market_value, count() AS unit_count
    FROM unit_intervals FINAL
    WHERE interval >= %(start)s AND interval < %(end)s
    GROUP BY interval, network_id, network_region, fueltech_id, fueltech_group_id
)
"""


def diff_day_rows(raw: tuple[Any, ...], agg: tuple[Any, ...], rel_tol: float = 1e-9, abs_tol: float = 1e-6) -> list[str]:
    """Names of compared columns where the raw and aggregate day summaries disagree."""
    bad: list[str] = []
    for name, r, a in zip(_COMPARE_COLS, raw, agg, strict=True):
        if name.endswith("_sum"):
            r, a = r or 0.0, a or 0.0
            if abs(r - a) > max(abs_tol, rel_tol * max(abs(r), abs(a))):
                bad.append(f"{name} raw={r!r} agg={a!r}")
        elif (r or 0) != (a or 0):
            bad.append(f"{name} raw={r!r} agg={a!r}")
    return bad


def compare_day(client: Any, day: date) -> list[str]:
    """Mismatch descriptions for one calendar day (empty = identical). Read-only."""
    params = {"start": datetime(day.year, day.month, day.day), "end": datetime(day.year, day.month, day.day) + timedelta(days=1)}
    raw = client.execute(_RAW_DAY_SQL, params)[0]
    agg = client.execute(_AGG_DAY_SQL, params)[0]
    return diff_day_rows(raw, agg)


def check_recent_sync(days: int = 2, retry_wait_s: float = 20.0, client: Any = None) -> dict[str, list[str]]:
    """Compare the last `days` network-local days (today included). Returns {day: mismatches}.

    A mismatching day is re-checked once after `retry_wait_s`: the incremental write lands the two
    tables a moment apart, so a single read can straddle a write.
    """
    client = client or get_clickhouse_client(timeout=300)
    today = datetime.now(ZoneInfo("Australia/Brisbane")).date()
    out: dict[str, list[str]] = {}
    for i in range(days):
        day = today - timedelta(days=i)
        bad = compare_day(client, day)
        if bad:
            time.sleep(retry_wait_s)
            bad = compare_day(client, day)
        if bad:
            out[day.isoformat()] = bad
    return out


async def check_recent(days: int = 2) -> dict[str, list[str]]:
    """Worker check (flag-gated by `CLICKHOUSE_AGG_TABLE_WRITE`): sentry message on any mismatch."""
    if not settings.clickhouse_agg_table_write:
        return {}
    try:
        mismatches = await asyncio.to_thread(check_recent_sync, days)
    except Exception as e:  # noqa: BLE001
        _report_failure("check", e)
        return {}
    if mismatches:
        summary = "; ".join(f"{d}: {', '.join(v)}" for d, v in mismatches.items())
        logger.error(f"{AGG_TABLE} differs from unit_intervals FINAL: {summary}")
        with sentry_sdk.new_scope() as scope:
            scope.fingerprint = ["fueltech-region-intervals-mismatch"]
            scope.set_tag("agg_table", AGG_TABLE)
            scope.set_context("mismatches", dict(mismatches))
            scope.capture_message(f"{AGG_TABLE} mismatch vs unit_intervals FINAL: {summary}"[:900], level="error")
    return mismatches
