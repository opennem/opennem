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

THE HOLDER RUNS IN ITS OWN THREAD
---------------------------------
Holding one transaction open for a whole rebuild needs two things the obvious implementation does
not give you. Both were observed failing on dev before this shape:

- `idle_in_transaction_session_timeout` is 5 minutes. `SET LOCAL` disables it for the holder's
  transaction only, so the pooled connection is handed back unchanged.
- The connection still has to carry traffic. The rebuild drives clickhouse-driver *synchronously*,
  so a single analysis query blocks the caller's event loop for minutes; a heartbeat coroutine
  sharing that loop never gets scheduled, the idle connection is dropped somewhere along the path
  (Tailscale, pgbouncer), and the lock silently disappears mid-rebuild. So the holder owns a private
  thread, a private event loop and a private engine, and none of them are touched by the rebuild.

If the connection drops anyway the holder reconnects and re-takes the lock. Re-taking it does not
undo the gap — a writer that probed a free lock in between is already running — so every gap is
counted on the handle and reported as critical at the end of the block. A lapsed guard otherwise
looks identical to a working one from the outside, and the rebuild's output would be trusted.

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
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.pool import NullPool

from opennem import settings
from opennem.db import get_read_session

logger = logging.getLogger("opennem.recordreactor.rebuild_guard")

# Fixed application-wide key. Any process that writes milestones must agree on it.
MILESTONE_REBUILD_LOCK_KEY = 640640640

# How often the holder pokes its connection. Short enough that a dropped connection is noticed and
# re-taken quickly, and that nothing along the path sees the connection as idle.
_HEARTBEAT_SECONDS = 20.0

# Granularity at which the holder notices the stop signal.
_POLL_SECONDS = 0.5

# Long enough for an incremental check that probed the lock just before it was taken to finish
# writing before the caller starts deleting.
_SETTLE_SECONDS = 60.0

# Bound on how long the caller waits for the holder thread to report back.
_ACQUIRE_TIMEOUT_SECONDS = 60.0


class MilestoneRebuildLockUnavailable(RuntimeError):
    """Raised when another rebuild already holds the lock."""


@asynccontextmanager
async def _holder_connection() -> AsyncIterator[AsyncConnection]:
    """A connection of the holder's very own, on the holder thread's event loop.

    Deliberately not `get_write_session()`: that engine's pool is bound to the caller's event loop,
    and asyncpg connections cannot be shared across loops. NullPool keeps this to exactly one
    connection with no pool state to leak back.
    """
    engine = create_async_engine(str(settings.db_url), poolclass=NullPool, pool_pre_ping=True)

    try:
        async with engine.connect() as connection:
            yield connection
    finally:
        await engine.dispose()


class MilestoneRebuildLock:
    """Handle for a held lock.

    Only the holder thread writes these; the caller reads them. Plain attributes are enough for a
    bool and a counter under CPython, and nothing branches on a torn read.

    - `lock_lost`: the guard stopped protecting the rebuild and did not get it back.
    - `protection_gaps`: how many times the lock was dropped and re-taken. Each gap is a window in
      which an incremental check could have probed a free lock and started writing, so a rebuild
      that ends with a gap is not proof of a clean table.
    """

    def __init__(self) -> None:
        self.lock_lost = False
        self.protection_gaps = 0

    @property
    def guard_intact(self) -> bool:
        return not self.lock_lost and self.protection_gaps == 0


async def _take_lock(connection: AsyncConnection) -> bool:
    # The transaction stays open for the whole rebuild, far past the 5-minute
    # idle_in_transaction_session_timeout dev and prod set. SET LOCAL scopes the override to this
    # transaction, so nothing leaks into the connection after it ends.
    await connection.execute(text("set local idle_in_transaction_session_timeout = 0"))
    result = await connection.execute(text("select pg_try_advisory_xact_lock(:key)"), {"key": MILESTONE_REBUILD_LOCK_KEY})

    return bool(result.scalar())


async def _hold_lock(
    handle: MilestoneRebuildLock,
    acquired: dict[str, object],
    ready: threading.Event,
    stop: threading.Event,
) -> None:
    """Take the lock, then keep the connection warm until asked to stop.

    Reconnects and re-takes the lock if the connection drops, which is the observed failure and not
    a hypothetical one. The lock is genuinely free during that gap, at most one heartbeat wide.
    """
    holding = False

    while not stop.is_set():
        try:
            async with _holder_connection() as connection:
                got = await _take_lock(connection)

                if not holding:
                    acquired["acquired"] = got
                    ready.set()
                    if not got:
                        return
                    holding = True
                    logger.info(f"Acquired milestone rebuild lock {MILESTONE_REBUILD_LOCK_KEY}")
                elif not got:
                    handle.lock_lost = True
                    logger.critical(
                        f"Lost milestone rebuild lock {MILESTONE_REBUILD_LOCK_KEY} to a dropped connection and could "
                        f"not re-acquire it — something else holds it and the incremental milestone writers are free "
                        f"to write into this rebuild."
                    )
                    return
                else:
                    logger.warning(
                        f"Re-acquired milestone rebuild lock {MILESTONE_REBUILD_LOCK_KEY} after a dropped connection. "
                        f"The lock was free in between, so an incremental check may have started writing."
                    )

                if not await _heartbeat_until_stopped(connection, stop):
                    handle.protection_gaps += 1
                    continue  # connection died — reconnect and re-take

                await connection.rollback()
                logger.info(f"Released milestone rebuild lock {MILESTONE_REBUILD_LOCK_KEY}")
                return
        except Exception as e:
            if not ready.is_set():
                acquired["error"] = True
                acquired["message"] = str(e)
                ready.set()
                raise

            handle.lock_lost = True
            logger.critical(f"Milestone rebuild lock holder failed ({e}) — the rebuild is no longer guarded")
            return

    # stop was set before the holder ever took the lock — nothing to release.
    if not ready.is_set():
        acquired["acquired"] = False
        ready.set()


async def _heartbeat_until_stopped(connection: AsyncConnection, stop: threading.Event) -> bool:
    """Poke the connection until stopped. False means it died and the caller should reconnect."""
    waited = 0.0

    while not stop.is_set():
        await asyncio.sleep(_POLL_SECONDS)
        waited += _POLL_SECONDS

        if waited < _HEARTBEAT_SECONDS:
            continue

        waited = 0.0

        try:
            await connection.execute(text("select 1"))
        except Exception as e:
            logger.warning(f"Milestone rebuild lock connection dropped ({e}) — reconnecting")
            return False

    return True


def _run_holder(
    handle: MilestoneRebuildLock,
    acquired: dict[str, object],
    ready: threading.Event,
    stop: threading.Event,
) -> None:
    try:
        asyncio.run(_hold_lock(handle, acquired, ready, stop))
    except Exception:
        ready.set()
        raise


@asynccontextmanager
async def milestone_rebuild_lock(settle_seconds: float = _SETTLE_SECONDS) -> AsyncIterator[MilestoneRebuildLock]:
    """Hold the milestone rebuild lock for the duration of the block.

    The transaction that owns the lock does no writes and lives on its own thread. The rebuild's own
    reads and writes use the normal sessions.

    Raises MilestoneRebuildLockUnavailable if another rebuild is already running, rather than
    queueing behind it: two full rebuilds in sequence is never what the operator wanted.

    Args:
        settle_seconds: wait between taking the lock and yielding, so an incremental run that
            probed the lock just before it was taken finishes before anything is deleted.
    """
    handle = MilestoneRebuildLock()
    acquired: dict[str, object] = {}
    ready = threading.Event()
    stop = threading.Event()

    thread = threading.Thread(
        target=_run_holder,
        args=(handle, acquired, ready, stop),
        name="milestone-rebuild-lock",
        daemon=True,
    )
    thread.start()

    # Everything from here on must be able to stop the thread. A cancellation between start() and
    # the try/finally below would otherwise leave a daemon thread holding the lock forever, blocking
    # every later rebuild and permanently skipping the incremental checker.
    try:
        if not await asyncio.to_thread(ready.wait, _ACQUIRE_TIMEOUT_SECONDS):
            raise MilestoneRebuildLockUnavailable(
                f"Timed out after {_ACQUIRE_TIMEOUT_SECONDS}s waiting to take advisory lock {MILESTONE_REBUILD_LOCK_KEY}"
            )

        if acquired.get("error"):
            raise RuntimeError(f"Could not take the milestone rebuild lock: {acquired.get('message')}")

        if not acquired.get("acquired"):
            raise MilestoneRebuildLockUnavailable(
                f"Another milestone rebuild holds advisory lock {MILESTONE_REBUILD_LOCK_KEY}. "
                f"Wait for it to finish rather than running two rebuilds over the same table."
            )

        if settle_seconds > 0:
            logger.info(f"Settling for {settle_seconds}s so any in-flight incremental check finishes")
            await asyncio.sleep(settle_seconds)

        # The holder can die during the settle. Entering the body then would delete the milestones
        # table with nothing holding the lock, which is the whole failure this guard exists to stop.
        if not handle.guard_intact or not thread.is_alive():
            raise MilestoneRebuildLockUnavailable(
                f"The milestone rebuild lock holder stopped before the rebuild began "
                f"(lock_lost={handle.lock_lost}, gaps={handle.protection_gaps}, alive={thread.is_alive()}). "
                f"Refusing to purge the milestones table unguarded."
            )

        yield handle
    finally:
        stop.set()
        await asyncio.to_thread(thread.join, _ACQUIRE_TIMEOUT_SECONDS)

        if thread.is_alive():
            logger.critical(
                f"The milestone rebuild lock holder did not stop within {_ACQUIRE_TIMEOUT_SECONDS}s and may still be "
                f"holding advisory lock {MILESTONE_REBUILD_LOCK_KEY}. Milestone writers will keep skipping until the "
                f"process exits."
            )

        if not handle.guard_intact:
            logger.critical(
                f"The milestone rebuild ran unguarded for part of its run (lock_lost={handle.lock_lost}, "
                f"gaps={handle.protection_gaps}). An incremental check may have written records the rebuild would "
                f"not have produced — verify the milestones table, and re-run the rebuild if in doubt."
            )


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
