"""Hotfix tests: seen-range update must bound its txn and skip (not wedge) on lock timeout / hang."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opennem.db import is_lock_timeout_error
from opennem.workers import facility_data_seen as fds

pytestmark = pytest.mark.asyncio


class _PgError(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__(sqlstate)
        self.sqlstate = sqlstate


def _fake_engine(execute: AsyncMock) -> tuple[MagicMock, list[str]]:
    conn = MagicMock()
    conn.execute = execute
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    engine = MagicMock()
    engine.begin = MagicMock(return_value=cm)
    return engine, []


async def test_guards_set_before_update() -> None:
    stmts: list[str] = []

    async def execute(stmt):
        stmts.append(str(stmt))

    engine, _ = _fake_engine(AsyncMock(side_effect=execute))
    with patch.object(fds, "db_connect", return_value=engine):
        assert await fds.update_facility_seen_range() is True

    assert "lock_timeout = '10s'" in stmts[0] + stmts[1] + stmts[2]
    joined = "\n".join(stmts[:3])
    assert "idle_in_transaction_session_timeout = '60s'" in joined
    assert "statement_timeout = '120s'" in joined
    assert "update units" in stmts[3]


async def test_lock_timeout_logs_and_skips() -> None:
    async def execute(stmt):
        if "update units" in str(stmt):
            raise _PgError("55P03")

    engine, _ = _fake_engine(AsyncMock(side_effect=execute))
    with patch.object(fds, "db_connect", return_value=engine):
        assert await fds.update_facility_seen_range() is False


async def test_other_errors_still_raise() -> None:
    async def execute(stmt):
        if "update units" in str(stmt):
            raise ValueError("boom")

    engine, _ = _fake_engine(AsyncMock(side_effect=execute))
    with patch.object(fds, "db_connect", return_value=engine), pytest.raises(ValueError):
        await fds.update_facility_seen_range()


async def test_bounded_wrapper_times_out_and_skips() -> None:
    async def hang(**_kwargs):
        await asyncio.sleep(30)
        return True

    with patch.object(fds, "update_facility_seen_range", hang), patch.object(fds, "SEEN_RANGE_RUN_TIMEOUT_SECONDS", 0.05):
        assert await fds.update_facility_seen_range_bounded(interval_window_days=7) is False


def test_is_lock_timeout_error_walks_chain() -> None:
    wrapped = RuntimeError("wrapped")
    wrapped.__cause__ = _PgError("57014")
    assert is_lock_timeout_error(wrapped)
    assert not is_lock_timeout_error(ValueError("x"))
