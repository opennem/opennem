"""Tests for the Postgres deadlock detection predicate and retry decorator."""

import pytest
from asyncpg.exceptions import DeadlockDetectedError

from opennem.db import is_deadlock_error, retry_on_deadlock


class _FakeOrig(Exception):
    """Stand-in for a DBAPI error exposing a sqlstate, like asyncpg adapters do."""

    def __init__(self, sqlstate: str) -> None:
        super().__init__("dbapi error")
        self.sqlstate = sqlstate


def test_raw_deadlock_is_detected() -> None:
    assert is_deadlock_error(DeadlockDetectedError("deadlock detected")) is True


def test_wrapped_deadlock_via_cause_chain_is_detected() -> None:
    # mimics sqlalchemy DBAPIError -> __cause__ -> asyncpg DeadlockDetectedError (the autoflush case)
    wrapper = RuntimeError("autoflush failed")
    wrapper.__cause__ = DeadlockDetectedError("deadlock detected")
    assert is_deadlock_error(wrapper) is True


def test_sqlstate_on_orig_is_detected() -> None:
    err = Exception("wrapped")
    err.orig = _FakeOrig("40P01")  # type: ignore[attr-defined]
    assert is_deadlock_error(err) is True


def test_non_deadlock_is_not_detected() -> None:
    assert is_deadlock_error(ValueError("nope")) is False
    assert is_deadlock_error(_FakeOrig("23505")) is False  # unique_violation, not a deadlock


def test_cause_cycle_terminates() -> None:
    a = Exception("a")
    b = Exception("b")
    a.__cause__ = b
    b.__cause__ = a  # self-referential chain must not loop forever
    assert is_deadlock_error(a) is False


@pytest.mark.asyncio
async def test_retry_on_deadlock_retries_then_succeeds() -> None:
    calls = {"n": 0}

    @retry_on_deadlock
    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise DeadlockDetectedError("deadlock detected")
        return "ok"

    assert await flaky() == "ok"
    assert calls["n"] == 3


@pytest.mark.asyncio
async def test_retry_on_deadlock_does_not_retry_other_errors() -> None:
    calls = {"n": 0}

    @retry_on_deadlock
    async def boom() -> None:
        calls["n"] += 1
        raise ValueError("not a deadlock")

    with pytest.raises(ValueError):
        await boom()
    assert calls["n"] == 1
