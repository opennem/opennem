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


async def _get_field(field: str) -> datetime | None:
    """Read one datetime field, or None if the row or field is absent."""
    async with get_read_session() as session:
        result = await session.execute(select(CrawlMeta).filter_by(spider_name=MILESTONE_INCREMENTAL_KEY))
        row = result.scalar_one_or_none()

    if not row or not row.data:
        return None

    raw: Any = row.data.get(field)

    if not raw:
        return None

    try:
        return datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        logger.error(f"Milestone watermark {field} is not a datetime: {raw!r}")
        return None


async def _set_field(field: str, value: datetime) -> None:
    """Write one datetime field, creating the row if it isn't there yet."""
    async with get_write_session() as session:
        result = await session.execute(select(CrawlMeta).filter_by(spider_name=MILESTONE_INCREMENTAL_KEY))
        row = result.scalar_one_or_none()

        if not row:
            row = CrawlMeta(spider_name=MILESTONE_INCREMENTAL_KEY, data={})

        if not row.data:
            row.data = {}

        row.data[field] = value.isoformat()

        session.add(row)
        await session.commit()


async def get_last_incremental_run() -> datetime | None:
    """Network time through which the incremental checker last completed a pass.

    None means it has never completed one that this code knew to record — a fresh deployment or a
    restored database, not evidence of downtime.
    """
    return await _get_field(LAST_RUN_FIELD)


async def set_last_incremental_run(checked_through: datetime) -> None:
    """Mark a completed pass. `checked_through` is the run's last completed network interval."""
    await _set_field(LAST_RUN_FIELD, checked_through)


async def get_gap_backfill_enqueued_at() -> datetime | None:
    """When a gap backfill was last queued, used to rate-limit the detector."""
    return await _get_field(GAP_BACKFILL_ENQUEUED_FIELD)


async def set_gap_backfill_enqueued_at(when: datetime) -> None:
    await _set_field(GAP_BACKFILL_ENQUEUED_FIELD, when)
