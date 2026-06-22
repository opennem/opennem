"""Determine the latest fully-settled interval for the live v4 data/market endpoints.

The most-recent interval present in ClickHouse is provisional: AEMO data for it can
still be settling when the aggregate first writes it, which surfaced as spurious `0`s
(emissions, renewable_proportion) that "heal" on a later poll (#575).

We treat `max(interval)` as an EXCLUSIVE upper bound. Combined with the query's
`interval < date_end`, this serves only intervals that already have a newer interval
behind them — i.e. intervals that have settled — and never the bleeding edge. Genuinely
absent trailing intervals are already omitted by the GROUP BY; this additionally drops
the present-but-provisional latest interval.

Only applied to the live case (no explicit `date_end`); explicit historical ranges are
left untouched. Falls back to the caller's `date_end` on empty table / CH error so the
endpoints never break.
"""

import logging
import time
from datetime import datetime
from typing import Any

from opennem.api.queries import QUERY_CONFIGS, QueryType
from opennem.db.clickhouse import execute_async
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.api.intervals")

# max(interval) only advances once per interval_size minutes, so a short TTL spares a CH
# round-trip on every (cache-missed) request without serving a meaningfully stale bound.
_CACHE_TTL_SECONDS = 30
_latest_interval_cache: dict[tuple[str, str], tuple[float, datetime | None]] = {}


async def _get_latest_interval(client: Any, network: NetworkSchema, base_table: str) -> datetime | None:
    """Latest interval present in `base_table` for `network`, or None on empty/error.

    Scoped to the last 7 days so the query stays bounded against the (interval-first)
    primary key while still covering WEM, which publishes ~24h late. `max()` needs no
    FINAL — dedup is irrelevant to the maximum timestamp. A table with no rows in the
    window (a multi-day ingestion outage) returns None and the caller falls back to its
    own date_end; that is harmless because such a table has no bleeding edge to exclude.
    """
    cache_key = (base_table, network.code)
    monotonic_now = time.monotonic()
    cached = _latest_interval_cache.get(cache_key)
    if cached is not None and cached[0] > monotonic_now:
        return cached[1]

    query = (
        f"SELECT max(interval) FROM {base_table} "  # noqa: S608 — base_table is an internal enum-derived constant
        "WHERE network_id IN %(network)s AND interval > now() - INTERVAL 7 DAY"
    )
    try:
        rows = await execute_async(client, query, {"network": tuple(network.get_network_codes())})
        latest = rows[0][0] if rows and rows[0][0] is not None else None
    except Exception as e:
        logger.warning(f"could not determine latest {base_table} interval for {network.code}: {e}")
        latest = None

    # `interval` is DateTime64(3) (naive) today; strip tz defensively so a future
    # 'UTC'-tagged column can't make min() raise on naive-vs-aware date_end.
    if latest is not None and latest.tzinfo is not None:
        latest = latest.replace(tzinfo=None)

    _latest_interval_cache[cache_key] = (monotonic_now + _CACHE_TTL_SECONDS, latest)
    return latest


async def cap_date_end_to_settled_interval(
    client: Any,
    network: NetworkSchema,
    query_type: QueryType,
    date_end: datetime,
) -> datetime:
    """Cap an exclusive-upper-bound `date_end` at the latest settled interval.

    Returns `date_end` unchanged only when the table is empty / on CH error. Otherwise
    caps at `max(interval)` unconditionally — with the query's `interval < date_end` this
    excludes the provisional latest interval. If the caller's window sat entirely on the
    bleeding edge (date_start >= the settled boundary) the query returns no rows and the
    endpoint 404s, which is the correct answer: an empty range beats serving a value we
    know is still settling.
    """
    base_table = QUERY_CONFIGS[query_type].base_table
    latest = await _get_latest_interval(client, network, base_table)
    if latest is None:
        return date_end
    return min(date_end, latest)
