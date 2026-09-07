"""The milestone rebuild lock has to actually stop the incremental writers.

A full rebuild empties the milestones table and refills it over many minutes. While a chain is
empty the incremental checker sees no previous record and mints the next bucket it looks at as a
brand new one — #640. These tests pin the three halves of the guard: the holder takes a
transaction-scoped advisory lock and releases it, the probe reports the lock as held, and the two
scheduled writers return without doing any work when it is.
"""

from contextlib import asynccontextmanager

import pytest

from opennem.recordreactor import rebuild_guard


class _FakeResult:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar(self) -> object:
        return self._value


class _FakeSession:
    """Records the SQL it is handed and hands back a canned pg_try_advisory_xact_lock answer."""

    def __init__(self, lock_acquired: bool = True) -> None:
        self.lock_acquired = lock_acquired
        self.statements: list[str] = []
        self.rolled_back = False

    async def execute(self, statement, params=None) -> _FakeResult:
        self.statements.append(str(statement))
        return _FakeResult(self.lock_acquired)

    async def rollback(self) -> None:
        self.rolled_back = True


def _patch_sessions(monkeypatch, session: _FakeSession) -> None:
    @asynccontextmanager
    async def _session_factory():
        yield session

    monkeypatch.setattr(rebuild_guard, "get_write_session", _session_factory)
    monkeypatch.setattr(rebuild_guard, "get_read_session", _session_factory)


@pytest.mark.asyncio
async def test_lock_is_transaction_scoped_and_released(monkeypatch) -> None:
    """A session-scoped lock is useless through pgbouncer — the key must be an xact lock, and the
    holding transaction must end on the way out."""
    session = _FakeSession(lock_acquired=True)
    _patch_sessions(monkeypatch, session)

    async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0):
        assert any("pg_try_advisory_xact_lock" in statement for statement in session.statements)
        assert not session.rolled_back

    assert session.rolled_back


@pytest.mark.asyncio
async def test_holder_disables_the_idle_in_transaction_timeout(monkeypatch) -> None:
    """The holder keeps a transaction open for the whole rebuild, well past the 5-minute
    idle_in_transaction_session_timeout dev and prod set. It must be disabled for that transaction,
    and with SET LOCAL so the pooled connection is handed back unchanged."""
    session = _FakeSession(lock_acquired=True)
    _patch_sessions(monkeypatch, session)

    async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0):
        pass

    timeout_statements = [s for s in session.statements if "idle_in_transaction_session_timeout" in s]
    assert timeout_statements, "holder never disabled the idle transaction timeout"
    assert all("set local" in s.lower() for s in timeout_statements)

    # It has to be in force before the lock is taken, or the timeout applies to the lock's own wait.
    assert session.statements.index(timeout_statements[0]) < next(
        i for i, s in enumerate(session.statements) if "pg_try_advisory_xact_lock" in s
    )


@pytest.mark.asyncio
async def test_lock_is_released_when_the_rebuild_raises(monkeypatch) -> None:
    """A crashed rebuild must not leave every scheduled milestone writer permanently skipping."""
    session = _FakeSession(lock_acquired=True)
    _patch_sessions(monkeypatch, session)

    with pytest.raises(RuntimeError, match="rebuild blew up"):
        async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0):
            raise RuntimeError("rebuild blew up")

    assert session.rolled_back


@pytest.mark.asyncio
async def test_second_rebuild_refuses_rather_than_queueing(monkeypatch) -> None:
    session = _FakeSession(lock_acquired=False)
    _patch_sessions(monkeypatch, session)

    with pytest.raises(rebuild_guard.MilestoneRebuildLockUnavailable):
        async with rebuild_guard.milestone_rebuild_lock(settle_seconds=0):
            pytest.fail("must not enter the block while another rebuild holds the lock")


@pytest.mark.asyncio
async def test_probe_reports_the_lock_as_held(monkeypatch) -> None:
    """The probe's own try-lock failing is the signal that a rebuild owns it."""
    _patch_sessions(monkeypatch, _FakeSession(lock_acquired=False))
    assert await rebuild_guard.milestone_rebuild_in_progress() is True

    _patch_sessions(monkeypatch, _FakeSession(lock_acquired=True))
    assert await rebuild_guard.milestone_rebuild_in_progress() is False


@pytest.mark.asyncio
async def test_probe_ends_its_own_transaction(monkeypatch) -> None:
    """The probe takes the lock to test it, so it must release it immediately or it becomes the
    thing it is checking for."""
    session = _FakeSession(lock_acquired=True)
    _patch_sessions(monkeypatch, session)

    await rebuild_guard.milestone_rebuild_in_progress()

    assert session.rolled_back


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
            yield
        finally:
            events.append("unlock")

    @asynccontextmanager
    async def _write_session():
        session = _FakeSession()

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
