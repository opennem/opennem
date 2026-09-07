"""Mutual exclusion between a milestone rebuild and the incremental milestone writers.

A full rebuild deletes the milestones table and re-derives it from ClickHouse over many minutes.
While the table is empty, `_map_row_to_records` sees no current record for a record_id and treats
the next bucket it looks at as a brand new record — so the 5-minute `task_update_milestones` cron
mints false records into the chains the rebuild is still refilling. That is how #640 happened, and
`bin/repair_demand_energy_milestones.py` has carried a post-hoc detector for it ever since.

The lock lives in Postgres, not Redis: the rebuild is normally run by hand from a laptop while the
incremental checker runs on the DigitalOcean worker, and those two do not share a Redis instance.
They do share the database.

It is a *transaction-scoped* advisory lock (`pg_advisory_xact_lock`). PG sits behind pgbouncer in
transaction-pooling mode, where session-scoped locks are useless twice over: commit hands the
backend back so the lock is dropped, and a second client sharing that backend re-acquires it
re-entrantly and sees success. A transaction-scoped lock is bound to a transaction, and pgbouncer
cannot hand that backend to anyone else until the transaction ends, so it behaves correctly.

The holder therefore keeps one transaction open for the whole rebuild, which collides with the
5-minute `idle_in_transaction_session_timeout` set on dev and prod. `SET LOCAL` disables that timeout
for the holder's transaction only, so nothing leaks back into the pooled connection. A heartbeat runs
alongside as a liveness check — it cannot be relied on for the timeout, because the rebuild drives
clickhouse-driver synchronously and a single long query blocks the event loop for minutes.

WHAT THIS DOES NOT COVER
------------------------
The writers probe the lock once, at the top of their run. A rebuild that starts in the moment
between a writer's probe and its first insert is not excluded, so `milestone_rebuild_lock()` waits
out a settle period after acquiring and before its caller purges anything. That covers a normal
incremental run, which takes seconds. It does not cover `_backfill_gap_if_needed` deciding to run a
multi-minute gap backlog. Holding a shared lock across a whole incremental run would close the
window properly, but it would pin one of ten pooled connections for the duration of a run that opens
more sessions inside itself — the deadlock shape CLAUDE.md warns about. The residual case is caught
after the fact by the surplus check in `bin/repair_demand_energy_milestones.py`.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opennem.db import get_read_session, get_write_session

logger = logging.getLogger("opennem.recordreactor.rebuild_guard")

# Fixed application-wide key. Any process that writes milestones must agree on it.
MILESTONE_REBUILD_LOCK_KEY = 640640640

# Liveness check only — the idle timeout is disabled outright, see the module docstring.
_HEARTBEAT_SECONDS = 60

# Long enough for an incremental check that probed the lock just before it was taken to finish
# writing before the caller starts deleting.
_SETTLE_SECONDS = 60


class MilestoneRebuildLockUnavailable(RuntimeError):
    """Raised when another rebuild already holds the lock."""


async def _heartbeat(session: AsyncSession, stop: asyncio.Event) -> None:
    """Liveness check on the holder's connection.

    Only this task touches the session between acquire and release, so there is no concurrent use of
    the AsyncSession. It is not what keeps the transaction alive — `SET LOCAL` disables the idle
    timeout — because it cannot run at all while the rebuild is inside a synchronous
    clickhouse-driver call, and those block the event loop for minutes at a time.
    """
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=_HEARTBEAT_SECONDS)
            return
        except TimeoutError:
            pass

        try:
            await session.execute(text("select 1"))
        except Exception as e:
            logger.critical(
                f"Milestone rebuild lock heartbeat failed ({e}). The advisory lock is no longer held and the "
                f"incremental milestone writers are free to write into the rebuild window."
            )
            return


@asynccontextmanager
async def milestone_rebuild_lock(settle_seconds: float = _SETTLE_SECONDS) -> AsyncIterator[None]:
    """Hold the milestone rebuild lock for the duration of the block.

    The transaction opened here does no writes — it exists only to own the lock. The rebuild's own
    reads and writes use their own sessions as usual.

    Raises MilestoneRebuildLockUnavailable if another rebuild is already running, rather than
    queueing behind it: two full rebuilds in sequence is never what the operator wanted.

    Args:
        settle_seconds: wait between taking the lock and yielding, so an incremental run that
            probed the lock just before it was taken finishes before anything is deleted.
    """
    async with get_write_session() as session:
        # The rebuild holds this transaction open for far longer than the 5-minute
        # idle_in_transaction_session_timeout dev and prod set. SET LOCAL scopes the override to
        # this transaction, so the pooled connection is handed back unchanged.
        await session.execute(text("set local idle_in_transaction_session_timeout = 0"))

        result = await session.execute(text("select pg_try_advisory_xact_lock(:key)"), {"key": MILESTONE_REBUILD_LOCK_KEY})

        if not result.scalar():
            raise MilestoneRebuildLockUnavailable(
                f"Another milestone rebuild holds advisory lock {MILESTONE_REBUILD_LOCK_KEY}. "
                f"Wait for it to finish rather than running two rebuilds over the same table."
            )

        logger.info(f"Acquired milestone rebuild lock {MILESTONE_REBUILD_LOCK_KEY}")

        if settle_seconds > 0:
            logger.info(f"Settling for {settle_seconds}s so any in-flight incremental check finishes")
            await asyncio.sleep(settle_seconds)

        stop = asyncio.Event()
        heartbeat = asyncio.create_task(_heartbeat(session, stop))

        try:
            yield
        finally:
            stop.set()
            heartbeat.cancel()
            try:
                await heartbeat
            except asyncio.CancelledError:
                pass
            # Rollback ends the transaction, which releases the lock. Nothing was written in it.
            await session.rollback()
            logger.info(f"Released milestone rebuild lock {MILESTONE_REBUILD_LOCK_KEY}")


async def milestone_rebuild_in_progress() -> bool:
    """True if a rebuild currently holds the lock.

    Probes with a transaction-scoped try-lock in a throwaway transaction, so the probe's own lock is
    released the moment it returns. Two probes overlapping inside that sub-millisecond window would
    see each other; the cost is one skipped incremental run, which the next cron tick repeats.
    """
    async with get_read_session() as session:
        try:
            result = await session.execute(text("select pg_try_advisory_xact_lock(:key)"), {"key": MILESTONE_REBUILD_LOCK_KEY})
            acquired = bool(result.scalar())
        finally:
            await session.rollback()

    return not acquired


async def skip_if_rebuild_in_progress(caller: str) -> bool:
    """Probe the lock and log the skip. Returns True when the caller should not run."""
    if await milestone_rebuild_in_progress():
        logger.warning(f"Milestone rebuild in progress, skipping {caller} — it will run again on the next schedule")
        return True

    return False
