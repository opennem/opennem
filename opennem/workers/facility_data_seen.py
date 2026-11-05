"""
For each facility calculate the first and last data seen dates from facility_scada

The min dates are run less regularly since data is less likely to grow in that direction
for most recent this is the last active date

@TODO move the utility functions into core/facility use this as only the worker
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from textwrap import dedent

from sqlalchemy import TextClause, text
from sqlalchemy.exc import DBAPIError

from opennem.db import apply_txn_guards, db_connect, is_lock_timeout_error, retry_on_deadlock
from opennem.queries.utils import duid_to_case
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.workers.facility_data_ranges")

# hard ceiling for one run: the txn guards below should fire first, this catches a hung connection
SEEN_RANGE_RUN_TIMEOUT_SECONDS = 150
SEEN_RANGE_STATEMENT_TIMEOUT_SECONDS = 120
# include_first_seen scans all of facility_scada (daily 01:32 cron): done in per-unit-chunk statements, give the
# whole run far more room. A single unchunked statement ran >1200s on dev and, behind pgbouncer's
# query_timeout=300, was killed with "connection was closed in the middle of operation: query timeout"
FIRST_SEEN_RUN_TIMEOUT_SECONDS = 3600
# must stay under pgbouncer query_timeout (300s on db-dev) so Postgres cancels cleanly before the pooler kills the conn
FIRST_SEEN_STATEMENT_TIMEOUT_SECONDS = 240
FIRST_SEEN_CHUNK_SIZE = 40
FIRST_SEEN_CHUNK_ATTEMPTS = 2


def get_update_seen_query(
    include_first_seen: bool = False,
    facility_codes: list[str] | None = None,
    interval_window_days: int | None = 7,
) -> TextClause:
    date_min: datetime | None = None

    if interval_window_days:
        date_min = get_today_opennem().replace(tzinfo=None) - timedelta(days=interval_window_days)

    __query = """
    update units u set
        {fs}data_first_seen = seen_query.data_first_seen,
        data_last_seen = seen_query.data_last_seen
    from (
        select
            fs.facility_code as code,
            {fs}min(fs.interval) as data_first_seen,
            max(fs.interval) as data_last_seen
        from facility_scada fs
        where
            -- any telemetered reading counts as "seen". a `> 0` filter pushed data_first_seen
            -- late for units that started idle (MM4 by 418 days) and excluded loads entirely (#615)
            fs.generated is not null
            and fs.is_forecast = false
            {facility_codes_query}
            {trading_interval_window}
        group by 1
    ) as seen_query
    where u.code = seen_query.code;
    """

    fs = "" if include_first_seen else "--"
    facility_codes_query = f"and fs.facility_code in ({duid_to_case(facility_codes)})" if facility_codes else ""

    trading_interval_window = ""

    if not include_first_seen:
        trading_interval_window = f"and fs.interval > '{date_min}'"

    query = __query.format(fs=fs, facility_codes_query=facility_codes_query, trading_interval_window=trading_interval_window)

    return text(dedent(query))


def _is_connection_lost(exc: BaseException) -> bool:
    """True for a dropped connection (pooler/DB restart or kill), safe to retry for idempotent statements"""
    return isinstance(exc, DBAPIError) and (exc.connection_invalidated or "connection was closed" in str(exc))


async def _run_seen_update(query: TextClause, statement_timeout_s: int) -> None:
    """Run one update in its own guarded transaction"""
    engine = db_connect()

    async with engine.begin() as conn:
        await apply_txn_guards(conn, statement_timeout_s=statement_timeout_s)
        logger.debug(query)
        await conn.execute(query)


async def _run_seen_update_retrying(query: TextClause, statement_timeout_s: int) -> None:
    """Retry once on a lost connection (update is idempotent); everything else, including timeouts, propagates"""
    for attempt in range(1, FIRST_SEEN_CHUNK_ATTEMPTS + 1):
        try:
            await _run_seen_update(query, statement_timeout_s)
            return
        except Exception as exc:
            if attempt == FIRST_SEEN_CHUNK_ATTEMPTS or not _is_connection_lost(exc):
                raise
            logger.warning(f"update_facility_seen_range connection lost (attempt {attempt}), retrying: {exc.__class__.__name__}")
            await asyncio.sleep(2 * attempt)


# unit codes are interpolated into the chunk's SQL text (duid_to_case does not escape), so only plain DUID-shaped codes pass
_SAFE_UNIT_CODE = re.compile(r"[A-Za-z0-9_.\-]+")


async def _get_unit_codes() -> list[str]:
    engine = db_connect()

    async with engine.begin() as conn:
        result = await conn.execute(text("select code from units order by code"))
        codes = [r[0] for r in result]

    safe = [c for c in codes if _SAFE_UNIT_CODE.fullmatch(c)]
    if len(safe) != len(codes):
        logger.warning(f"update_facility_seen_range skipped {len(codes) - len(safe)} unit codes with unexpected characters")
    return safe


# @profile_task(send_slack=True)
@retry_on_deadlock
async def update_facility_seen_range(
    include_first_seen: bool = False,
    facility_codes: list[str] | None = None,
    interval_window_days: int | None = 7,
) -> bool:
    """Updates last seen and first seen. For each facility updates the date the facility
    was seen for the first and last time in the power data from FacilityScada.

    The full-history (include_first_seen) scan runs in chunks of units, one short transaction each, so no
    statement outlives pooler/statement timeouts and a failed chunk is skipped (retried next cycle).

    Args:
        include_first_seen (bool, optional): Include earliest seen time. Defaults to False.
        facility_codes (Optional[List[str]], optional): List of facility codes to update. Defaults to None.

    Returns:
        bool: Ran successfuly (False if any chunk was skipped on lock/statement timeout)
    """

    # a 2h `idle in transaction` session holding units row locks wedged the worker (2026-11-03):
    # bound lock wait, statement time and idle-in-txn so it self-releases; skip + retry next cycle
    if include_first_seen and not facility_codes:
        codes = await _get_unit_codes()
        chunks: list[list[str] | None] = [
            codes[i : i + FIRST_SEEN_CHUNK_SIZE] for i in range(0, len(codes), FIRST_SEEN_CHUNK_SIZE)
        ]
    else:
        chunks = [facility_codes]

    statement_timeout_s = FIRST_SEEN_STATEMENT_TIMEOUT_SECONDS if include_first_seen else SEEN_RANGE_STATEMENT_TIMEOUT_SECONDS
    ok = True

    for chunk in chunks:
        query = get_update_seen_query(
            include_first_seen=include_first_seen,
            facility_codes=chunk,
            interval_window_days=interval_window_days,
        )
        try:
            await _run_seen_update_retrying(query, statement_timeout_s)
        except Exception as exc:
            if is_lock_timeout_error(exc):
                logger.warning(
                    f"update_facility_seen_range chunk skipped: lock/statement timeout ({exc.__class__.__name__}), "
                    "retry next cycle"
                )
                ok = False
                continue
            raise

    return ok


async def update_facility_seen_range_bounded(**kwargs) -> bool:
    """update_facility_seen_range under a hard asyncio timeout; a timeout logs and skips (cron retries next cycle)."""
    run_timeout = FIRST_SEEN_RUN_TIMEOUT_SECONDS if kwargs.get("include_first_seen") else SEEN_RANGE_RUN_TIMEOUT_SECONDS
    try:
        return await asyncio.wait_for(update_facility_seen_range(**kwargs), timeout=run_timeout)
    except TimeoutError:
        logger.error(f"update_facility_seen_range timed out after {run_timeout}s, skipped")
        return False


if __name__ == "__main__":
    import asyncio

    asyncio.run(update_facility_seen_range(include_first_seen=True, interval_window_days=7))
