"""Durable state for milestone detection: when the incremental checker last completed a pass.

The gap backfill exists to cover worker downtime, so staleness has to be measured against the last
time the checker RAN. It used to be measured against `max(milestones.interval)` — the newest
record — and a healthy system routinely goes more than a day without setting one, so the gap never
closed and the backfill re-enqueued itself indefinitely (#658).

WHY POSTGRES AND NOT REDIS
--------------------------
The arq worker calls `redis.flushdb()` on startup (`opennem.tasks.app.startup`), which wipes the
whole database, not just the queue. A watermark held in redis would be gone after every deploy or
restart, the detector would see no watermark, and the loop would come back on the next reboot.

`crawl_meta` is the project's existing small durable key/value table (`spider_name` + a JSONB
blob), so this needs no migration. The row is keyed by `MILESTONE_INCREMENTAL_KEY`, which is not a
spider name — that is deliberate and the only liberty taken with the table.

LAST SETTLED INTERVAL
---------------------
The same row carries, per network, the last settled interval the checker has covered with rooftop
in it (#662). The interval window used to start a fixed settle-lag before the current settled
interval, so when the settled interval jumped further than that between two runs (a restart, a
slow rooftop crawl, rooftop landing in a batch) the intervals in between were never checked with
rooftop included — dev missed QLD1 renewables at 8,360.7 MW on 2026-09-22 12:30 that way. The
window now starts from this value instead. It lives next to `last_run_at` so both are written by
the one upsert at the end of a pass, and it only ever moves forward.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import CrawlMeta

logger = logging.getLogger("opennem.recordreactor.watermark")

# crawl_meta row holding the incremental checker's state
MILESTONE_INCREMENTAL_KEY = "milestones.incremental"

# End of the last completed incremental pass, in network time
LAST_RUN_FIELD = "last_run_at"

# When a gap backfill was last handed to the queue, in network time
GAP_BACKFILL_ENQUEUED_FIELD = "gap_backfill_enqueued_at"

# Last settled interval each network's pass has covered, as {network code: iso datetime} (#662).
# Absent (a row written before #662) means the window falls back to the fixed settle lag.
LAST_SETTLED_FIELD = "last_settled_interval"


def _parse_datetime(field: str, raw: Any) -> datetime | None:
    if not raw:
        return None

    try:
        return datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        logger.error(f"Milestone watermark {field} is not a datetime: {raw!r}")
        return None


async def _get_data() -> dict[str, Any]:
    """The watermark row's JSON blob, or {} if the row isn't there yet."""
    async with get_read_session() as session:
        result = await session.execute(select(CrawlMeta).filter_by(spider_name=MILESTONE_INCREMENTAL_KEY))
        row = result.scalar_one_or_none()

    data: Any = row.data if row else None

    if not data:
        return {}

    return dict(data)


async def _get_field(field: str) -> datetime | None:
    """Read one datetime field, or None if the row or field is absent."""
    data = await _get_data()
    return _parse_datetime(field, data.get(field))


async def _set_fields(updates: dict[str, Any]) -> None:
    """Write several fields in one upsert, creating the row if it isn't there yet.

    `updates` may hold a callable, which is given the field's current value and returns the new
    one — so a field can be merged against what is stored inside the same transaction.
    """
    async with get_write_session() as session:
        result = await session.execute(select(CrawlMeta).filter_by(spider_name=MILESTONE_INCREMENTAL_KEY))
        row = result.scalar_one_or_none()

        if not row:
            row = CrawlMeta(spider_name=MILESTONE_INCREMENTAL_KEY, data={})

        if not row.data:
            row.data = {}

        for field, value in updates.items():
            row.data[field] = value(row.data.get(field)) if callable(value) else value

        session.add(row)
        await session.commit()


async def _set_field(field: str, value: datetime) -> None:
    """Write one datetime field, creating the row if it isn't there yet."""
    await _set_fields({field: value.isoformat()})


def parse_settled_intervals(raw: Any) -> dict[str, datetime]:
    """The stored per-network settled intervals; anything unreadable is dropped, not fatal."""
    if not isinstance(raw, dict):
        return {}

    parsed = {code: _parse_datetime(f"{LAST_SETTLED_FIELD}.{code}", value) for code, value in raw.items()}

    return {code: value for code, value in parsed.items() if value is not None}


def merge_settled_intervals(stored: Any, covered: dict[str, datetime]) -> dict[str, str]:
    """Advance the stored settled intervals to what this pass covered, never backwards.

    The settled interval can regress between runs — rooftop missing for a region drops it back to
    the fixed-lag fallback — and moving the watermark back with it would just re-scan intervals
    that are already covered. Networks this pass didn't cover keep their stored value.
    """
    merged = parse_settled_intervals(stored)

    for code, value in covered.items():
        current = merged.get(code)
        merged[code] = value if current is None else max(current, value)

    return {code: value.isoformat() for code, value in merged.items()}


async def get_last_incremental_run() -> datetime | None:
    """Network time through which the incremental checker last completed a pass.

    None means it has never completed one that this code knew to record — a fresh deployment or a
    restored database, not evidence of downtime.
    """
    return await _get_field(LAST_RUN_FIELD)


async def set_last_incremental_run(checked_through: datetime, settled_intervals: dict[str, datetime] | None = None) -> None:
    """Mark a completed pass. `checked_through` is the run's last completed network interval.

    `settled_intervals` is the settled interval each network's pass covered, keyed by network
    code. Both land in one upsert; the settled intervals only ever move forward (#662).
    """
    updates: dict[str, Any] = {LAST_RUN_FIELD: checked_through.isoformat()}

    if settled_intervals:
        updates[LAST_SETTLED_FIELD] = lambda stored: merge_settled_intervals(stored, settled_intervals)

    await _set_fields(updates)


async def get_last_settled_intervals() -> dict[str, datetime]:
    """Last settled interval the checker covered, per network code. {} if never recorded (#662)."""
    data = await _get_data()
    return parse_settled_intervals(data.get(LAST_SETTLED_FIELD))


async def get_gap_backfill_enqueued_at() -> datetime | None:
    """When a gap backfill was last queued, used to rate-limit the detector."""
    return await _get_field(GAP_BACKFILL_ENQUEUED_FIELD)


async def set_gap_backfill_enqueued_at(when: datetime) -> None:
    await _set_field(GAP_BACKFILL_ENQUEUED_FIELD, when)
