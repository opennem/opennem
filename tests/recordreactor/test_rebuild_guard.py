"""The milestone rebuild lock has to actually stop the incremental writers.

A full rebuild empties the milestones table and refills it over many minutes. While a chain is
empty the incremental checker sees no previous record and mints the next bucket it looks at as a
brand new one — #640. These tests pin the three halves of the guard: the holder takes and keeps a
transaction-scoped advisory lock, the probe reports the lock as held, and the two scheduled writers
return without doing any work when it is.

The holder deliberately runs on its own thread with its own event loop and its own connection,
because the rebuild blocks the caller's loop inside synchronous clickhouse-driver calls for minutes
at a time. These tests run the real threading against a fake connection.
"""

from contextlib import asynccontextmanager

import pytest

from opennem.recordreactor import rebuild_guard


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar(self) -> object:
        return self._value


class _FakeConnection:
    """Records the SQL it is handed and answers the try-lock with a canned value.

    `die_after_heartbeats` makes `select 1` raise, which is how a dropped connection presents.
    """

    def __init__(self, lock_acquired: bool = True, die_after_heartbeats: int | None = None) -> None:
        self.lock_acquired = lock_acquired
        self.die_after_heartbeats = die_after_heartbeats
        self.statements: list[str] = []
        self.heartbeats = 0
        self.rolled_back = False

    async def execute(self, statement, params=None) -> _FakeResult:
        sql = str(statement)
        self.statements.append(sql)

        if sql.strip() == "select 1":
            self.heartbeats += 1
            if self.die_after_heartbeats is not None and self.heartbeats > self.die_after_heartbeats:
                raise ConnectionResetError("connection is closed")

        return _FakeResult(self.lock_acquired)

    async def rollback(self) -> None:
        self.rolled_back = True


def _patch_holder(monkeypatch, connections: list[_FakeConnection]) -> list[_FakeConnection]:
    """Hand the holder each connection in turn, so reconnects can be observed."""
    handed: list[_FakeConnection] = []
    remaining = list(connections)

    @asynccontextmanager
    async def _connection():
        connection = remaining.pop(0) if remaining else connections[-1]
        handed.append(connection)
        yield connection

    monkeypatch.setattr(rebuild_guard, "_holder_connection", _connection)
    # Real threads and a real loop, but no reason to wait 20 seconds for a heartbeat.
    monkeypatch.setattr(rebuild_guard, "_HEARTBEAT_SECONDS", 0.02)
    monkeypatch.setattr(rebuild_guard, "_POLL_SECONDS", 0.01)

    return handed


def _patch_probe(monkeypatch, connection: _FakeConnection) -> None:
    @asynccontextmanager
    async def _session():
        yield connection

    monkeypatch.setattr(rebuild_guard, "get_read_session", _session)


@pytest.mark.asyncio
async def test_lock_is_transaction_scoped_and_released(monkeypatch) -> None:
    """A session-scoped lock is useless through pgbouncer — the key must be an xact lock, and the
    holding transaction must end on the way out."""
    connection = _FakeConnection()
    _patch_holder(monkeypatch, [connection])

    async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0) as lock:
        assert any("pg_try_advisory_xact_lock" in statement for statement in connection.statements)
        assert not connection.rolled_back
        assert not lock.lock_lost

    assert connection.rolled_back


@pytest.mark.asyncio
async def test_holder_disables_the_idle_in_transaction_timeout(monkeypatch) -> None:
    """The holder keeps a transaction open for the whole rebuild, well past the 5-minute
    idle_in_transaction_session_timeout dev and prod set. It must be disabled for that transaction,
    and with SET LOCAL so the connection is left unchanged."""
    connection = _FakeConnection()
    _patch_holder(monkeypatch, [connection])

    async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0):
        pass

    timeout_statements = [s for s in connection.statements if "idle_in_transaction_session_timeout" in s]
    assert timeout_statements, "holder never disabled the idle transaction timeout"
    assert all("set local" in s.lower() for s in timeout_statements)

    # It has to be in force before the lock is taken, or the timeout applies to the lock's own wait.
    assert connection.statements.index(timeout_statements[0]) < next(
        i for i, s in enumerate(connection.statements) if "pg_try_advisory_xact_lock" in s
    )


@pytest.mark.asyncio
async def test_heartbeat_survives_a_blocked_caller_loop(monkeypatch) -> None:
    """This is the regression test for the failure that took the guard out on dev.

    The rebuild drives clickhouse-driver synchronously, so the caller's event loop is blocked solid
    for minutes at a time. A heartbeat coroutine sharing that loop never runs, the connection is
    dropped, and the lock silently disappears. Blocking the loop here with `time.sleep` must not
    stop the holder, because the holder is on another thread with its own loop.
    """
    import time

    connection = _FakeConnection()
    _patch_holder(monkeypatch, [connection])

    async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0) as lock:
        before = connection.heartbeats
        time.sleep(0.4)  # not asyncio.sleep — the loop must be genuinely blocked
        during = connection.heartbeats

    assert during > before, "holder stopped heartbeating while the caller's event loop was blocked"
    assert lock.guard_intact


@pytest.mark.asyncio
async def test_holder_reconnects_and_retakes_a_dropped_lock(monkeypatch) -> None:
    """Observed on dev: the holder's connection was dropped two minutes into a rebuild. Reconnecting
    and re-taking the lock beats leaving the rest of the rebuild unguarded — but the lock really was
    free in between, so the run must not be reported as cleanly guarded."""
    dropped = _FakeConnection(die_after_heartbeats=1)
    replacement = _FakeConnection()
    handed = _patch_holder(monkeypatch, [dropped, replacement])

    async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0) as lock:
        await _wait_until(lambda: replacement in handed)

    assert handed[:2] == [dropped, replacement]
    assert any("pg_try_advisory_xact_lock" in s for s in replacement.statements)
    assert not lock.lock_lost
    assert lock.protection_gaps == 1
    assert not lock.guard_intact
    assert replacement.rolled_back


@pytest.mark.asyncio
async def test_body_is_refused_if_the_holder_dies_during_the_settle(monkeypatch) -> None:
    """The settle window is dead time for the caller but not for the holder. Entering the body with
    a dead holder would purge the milestones table with nothing holding the lock."""
    dropped = _FakeConnection(die_after_heartbeats=0)
    stolen = _FakeConnection(lock_acquired=False)
    _patch_holder(monkeypatch, [dropped, stolen])

    with pytest.raises(rebuild_guard.MilestoneRebuildLockUnavailable, match="stopped before the rebuild began"):
        async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0.3):
            pytest.fail("must not purge the milestones table with a dead lock holder")


@pytest.mark.asyncio
async def test_cancellation_during_acquire_stops_the_holder(monkeypatch) -> None:
    """The holder is a daemon thread. A cancellation before the try/finally would strand it holding
    the lock, permanently skipping every incremental check for the life of the process."""
    import asyncio

    connection = _FakeConnection()
    _patch_holder(monkeypatch, [connection])

    async def _enter() -> None:
        async with rebuild_guard.milestone_rebuild_lock(settle_seconds=30):
            pytest.fail("should have been cancelled during the settle")

    task = asyncio.create_task(_enter())
    await _wait_until(lambda: connection.heartbeats >= 1)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    await _wait_until(lambda: connection.rolled_back)
    assert connection.rolled_back


@pytest.mark.asyncio
async def test_losing_the_lock_to_someone_else_is_reported(monkeypatch) -> None:
    """If the re-acquire loses the race the rebuild is genuinely unguarded, and a lapsed guard looks
    identical to a working one unless it is surfaced."""
    dropped = _FakeConnection(die_after_heartbeats=1)
    stolen = _FakeConnection(lock_acquired=False)
    handed = _patch_holder(monkeypatch, [dropped, stolen])

    async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0) as lock:
        await _wait_until(lambda: lock.lock_lost)

    assert stolen in handed
    assert lock.lock_lost


@pytest.mark.asyncio
async def test_lock_is_released_when_the_rebuild_raises(monkeypatch) -> None:
    """A crashed rebuild must not leave every scheduled milestone writer permanently skipping."""
    connection = _FakeConnection()
    _patch_holder(monkeypatch, [connection])

    with pytest.raises(RuntimeError, match="rebuild blew up"):
        async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0):
            raise RuntimeError("rebuild blew up")

    assert connection.rolled_back


@pytest.mark.asyncio
async def test_second_rebuild_refuses_rather_than_queueing(monkeypatch) -> None:
    connection = _FakeConnection(lock_acquired=False)
    _patch_holder(monkeypatch, [connection])

    with pytest.raises(rebuild_guard.MilestoneRebuildLockUnavailable):
        async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0):
            pytest.fail("must not enter the block while another rebuild holds the lock")


@pytest.mark.asyncio
async def test_probe_reports_the_lock_as_held(monkeypatch) -> None:
    """The probe's own try-lock failing is the signal that a rebuild owns it."""
    _patch_probe(monkeypatch, _FakeConnection(lock_acquired=False))
    assert await rebuild_guard.milestone_rebuild_in_progress() is True

    _patch_probe(monkeypatch, _FakeConnection(lock_acquired=True))
    assert await rebuild_guard.milestone_rebuild_in_progress() is False


@pytest.mark.asyncio
async def test_probe_ends_its_own_transaction(monkeypatch) -> None:
    """The probe takes the lock to test it, so it must release it immediately or it becomes the
    thing it is checking for."""
    connection = _FakeConnection()
    _patch_probe(monkeypatch, connection)

    await rebuild_guard.milestone_rebuild_in_progress()

    assert connection.rolled_back


@pytest.mark.asyncio
async def test_incremental_check_stands_down_during_a_rebuild(monkeypatch) -> None:
    """The whole check, gap backfill included, must be skipped — the backfill writes milestones too."""
    from opennem.recordreactor import incremental

    async def _in_progress(caller: str) -> bool:
        return True

    def _boom(*args, **kwargs):
        raise AssertionError("incremental check ran during a rebuild")

    monkeypatch.setattr(incremental, "skip_if_rebuild_in_progress", _in_progress)
    monkeypatch.setattr(incremental, "_backfill_gap_if_needed", _boom)
    monkeypatch.setattr(incremental, "get_clickhouse_client", _boom)

    assert await incremental.run_incremental_milestone_check(alert_slack=False) == []


@pytest.mark.asyncio
async def test_reconciliation_stands_down_during_a_rebuild(monkeypatch) -> None:
    """Reconciliation inserts into chains it believes are missing records — mid-rebuild they all are."""
    from opennem.recordreactor import backlog

    async def _in_progress(caller: str) -> bool:
        return True

    def _boom(*args, **kwargs):
        raise AssertionError("reconciliation ran during a rebuild")

    monkeypatch.setattr(backlog, "skip_if_rebuild_in_progress", _in_progress)
    monkeypatch.setattr(backlog, "run_milestone_analysis", _boom)

    await backlog.run_milestone_reconciliation()


@pytest.mark.asyncio
async def test_refresh_backlog_purges_inside_the_lock(monkeypatch) -> None:
    """The delete is the dangerous statement — it must not run before the lock is held."""
    from opennem.recordreactor import backlog

    events: list[str] = []

    @asynccontextmanager
    async def _lock():
        events.append("lock")
        try:
            yield rebuild_guard.MilestoneRebuildLock()
        finally:
            events.append("unlock")

    @asynccontextmanager
    async def _write_session():
        session = _FakeConnection()

        async def _commit() -> None:
            events.append("commit")

        session.commit = _commit  # type: ignore[attr-defined]
        yield session
        events.append(f"delete:{'delete from milestones' in ' '.join(session.statements)}")

    async def _analysis(*args, **kwargs):
        events.append("analysis")
        return []

    monkeypatch.setattr(backlog, "milestone_rebuild_lock", _lock)
    monkeypatch.setattr(backlog, "get_write_session", _write_session)
    monkeypatch.setattr(backlog, "run_milestone_analysis", _analysis)

    await backlog.run_milestone_analysis_backlog(refresh=True, confirm_delete=True)

    assert events == ["lock", "commit", "delete:True", "analysis", "unlock"]


async def _wait_until(predicate, timeout: float = 5.0) -> None:
    """The holder runs on another thread, so its progress has to be waited for, not assumed."""
    import asyncio

    deadline = asyncio.get_running_loop().time() + timeout

    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return
        await asyncio.sleep(0.01)

    raise AssertionError("holder thread did not reach the expected state in time")
