"""In-memory set of known facility and unit codes, used to reject unknown-code data requests before auth/ClickHouse (#646).

The set is refreshed from Postgres in a background task and never loaded on the request path. It fails OPEN:
until the first load succeeds nothing is rejected, so a cold cache can never turn a valid request into a 404.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field

from sqlalchemy import select

from opennem.db import get_read_session
from opennem.db.clickhouse import execute_async
from opennem.db.models.opennem import Facility, Unit

logger = logging.getLogger("opennem.api.known_codes")

REFRESH_INTERVAL_SECONDS = 300
# a miss on a set older than this passes through (fail open) and triggers a refresh, so a facility added since
# the last load is never rejected for longer than this
MISS_REFRESH_AFTER_SECONDS = 60
_LOAD_TIMEOUT_SECONDS = 30


@dataclass
class _KnownCodes:
    facilities: frozenset[str] = frozenset()
    units: frozenset[str] = frozenset()
    loaded_at: float | None = None
    refresh_task: asyncio.Task[None] | None = field(default=None, repr=False)


_state = _KnownCodes()


async def _load_codes() -> tuple[frozenset[str], frozenset[str]]:
    """Union of Postgres and ClickHouse codes: CMS-created facilities (e.g. `0BUNGAMA`) exist in ClickHouse but not Postgres."""
    async with get_read_session() as session:
        facilities = set((await session.execute(select(Facility.code))).scalars().all())
        units = {c for c in (await session.execute(select(Unit.code))).scalars().all() if c}

    # execute_async runs on a worker thread with its own thread-local client; the client arg is unused
    rows = await execute_async(None, "SELECT DISTINCT facility_code, unit_code FROM unit_intervals_daily_mv")  # pyright: ignore[reportArgumentType]
    facilities.update(r[0] for r in rows if r[0])
    units.update(r[1] for r in rows if r[1])
    return frozenset(facilities), frozenset(units)


async def refresh_known_codes() -> None:
    """Reload the sets. Keeps the previous sets on any failure or an empty result."""
    try:
        facilities, units = await asyncio.wait_for(_load_codes(), timeout=_LOAD_TIMEOUT_SECONDS)
    except Exception as e:
        logger.warning(f"known codes refresh failed: {e}")
        return

    if not facilities or not units:
        logger.warning("known codes refresh returned an empty set, keeping previous")
        return

    _state.facilities, _state.units, _state.loaded_at = facilities, units, time.monotonic()
    logger.debug(f"known codes loaded: {len(facilities)} facilities, {len(units)} units")


async def _refresh_loop() -> None:
    while True:
        await refresh_known_codes()
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


def start_known_codes_refresher() -> asyncio.Task[None]:
    """Start the periodic refresh (first load happens in the task, not on startup)."""
    return asyncio.create_task(_refresh_loop(), name="known-codes-refresh")


def _schedule_refresh() -> None:
    """Single-flight refresh kicked from a request that missed."""
    if _state.refresh_task and not _state.refresh_task.done():
        return
    _state.refresh_task = asyncio.create_task(refresh_known_codes(), name="known-codes-miss-refresh")


def _all_unknown(requested: list[str], known: frozenset[str]) -> bool:
    return bool(requested) and not any(code in known for code in requested)


def has_unknown_codes(facility_codes: list[str], unit_codes: list[str]) -> bool:
    """True when the request filters can match nothing: every requested facility (or every requested unit) is unknown.

    Partial matches are not rejected (the query returns the known ones). Fails open when not loaded.
    """
    if _state.loaded_at is None:
        return False

    if not (_all_unknown(facility_codes, _state.facilities) or _all_unknown(unit_codes, _state.units)):
        return False

    if time.monotonic() - _state.loaded_at > MISS_REFRESH_AFTER_SECONDS:
        _schedule_refresh()
        return False

    return True
