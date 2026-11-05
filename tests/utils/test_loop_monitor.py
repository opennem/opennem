"""Event loop lag monitor: detection, no false positives, rate limit, shutdown, executor depth."""

import asyncio
import logging
import threading
import time
from typing import Any

import pytest

from opennem.utils import loop_monitor
from opennem.utils.loop_monitor import LoopMonitor, get_executor_depth

pytestmark = pytest.mark.asyncio


def _mon(**kw) -> LoopMonitor:
    kw.setdefault("interval_s", 0.02)
    kw.setdefault("threshold_ms", 250.0)
    return LoopMonitor("test", **kw)


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


async def test_detects_blocking_call() -> None:
    mon = _mon()
    handler = _ListHandler()
    loop_monitor.logger.addHandler(handler)  # caplog misses this logger (no propagation)
    mon.start()
    await asyncio.sleep(0.1)
    time.sleep(0.4)  # blocks the loop
    await asyncio.sleep(0.1)
    await mon.stop()
    loop_monitor.logger.removeHandler(handler)
    assert mon.stats()["lag_max_ms"] >= 300
    assert mon.warnings_emitted == 1
    assert any("event loop lag" in m for m in handler.messages)


async def test_idle_no_false_positive() -> None:
    mon = _mon()
    mon.start()
    await asyncio.sleep(0.5)
    await mon.stop()
    assert mon.warnings_emitted == 0
    assert mon.stats()["lag_max_ms"] < 250


async def test_rate_limited() -> None:
    mon = _mon(warn_rate_limit_s=10.0)
    for i in range(5):
        mon._tick(500.0, 100.0 + i)
    assert mon.warnings_emitted == 1
    mon._tick(500.0, 111.0)  # past the window
    assert mon.warnings_emitted == 2


async def test_threshold_configurable() -> None:
    low = _mon(threshold_ms=100.0)
    high = _mon(threshold_ms=1000.0)
    for m in (low, high):
        m._tick(300.0, 50.0)
    assert low.warnings_emitted == 1
    assert high.warnings_emitted == 0


async def test_severe_captures_message(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []
    monkeypatch.setattr(loop_monitor.sentry_sdk.Scope, "capture_message", lambda self, msg, level=None: sent.append(msg))
    mon = _mon()
    mon._tick(500.0, 100.0)
    assert sent == []
    mon._tick(2500.0, 200.0)
    assert len(sent) == 1


async def test_clean_shutdown() -> None:
    mon = _mon()
    mon.start()
    task = mon._task
    await asyncio.sleep(0.05)
    await mon.stop()
    assert task is not None and task.done()
    await mon.stop()  # idempotent


async def test_tick_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(loop_monitor.sentry_sdk, "add_breadcrumb", boom)
    _mon()._tick(999.0, 10.0)


async def test_report_emitted_after_interval() -> None:
    reports: list[dict[str, Any]] = []
    mon = _mon(report_interval_s=5.0, on_report=reports.append)
    mon._last_report = 0.0
    mon._tick(1.0, 6.0)
    assert len(reports) == 1 and "lag_p99_ms" in reports[0]


async def test_executor_depth() -> None:
    assert get_executor_depth() is None or isinstance(get_executor_depth(), int)
    await asyncio.to_thread(lambda: None)  # creates default executor
    depth = get_executor_depth()
    assert depth is None or depth >= 0
    assert get_executor_depth(object()) is None  # pyright: ignore


# stall watchdog


def _watch_mon(**kw) -> LoopMonitor:
    kw.setdefault("stack_threshold_ms", 1000.0)
    kw.setdefault("watchdog_interval_s", 0.05)
    return _mon(**kw)


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    monkeypatch.setattr(loop_monitor.sentry_sdk.Scope, "capture_event", lambda self, event, *a, **k: events.append(event))
    return events


def _blocking_in_coroutine_marker() -> None:
    time.sleep(1.5)


async def test_watchdog_captures_real_blocker(captured: list[dict[str, Any]]) -> None:
    mon = _watch_mon()
    mon.start()
    await asyncio.sleep(0.1)
    _blocking_in_coroutine_marker()  # blocks the loop thread
    await asyncio.sleep(0.1)
    await mon.stop()
    assert mon.stack_captures >= 1
    frames = captured[0]["exception"]["values"][0]["stacktrace"]["frames"]
    assert frames[-1]["function"] == "_blocking_in_coroutine_marker"
    assert any(f["function"] == "test_watchdog_captures_real_blocker" for f in frames)
    assert "test_loop_monitor.py" in frames[-1]["filename"]
    assert captured[0]["fingerprint"][0] == "event-loop-stall"
    assert "_blocking_in_coroutine_marker" in captured[0]["extra"]["stack"]
    assert len(frames) <= loop_monitor.STACK_MAX_FRAMES


async def test_watchdog_idle_no_capture(captured: list[dict[str, Any]]) -> None:
    mon = _watch_mon(stack_threshold_ms=300.0)
    mon.start()
    await asyncio.sleep(0.6)
    await mon.stop()
    assert mon.stack_captures == 0 and captured == []


async def test_watchdog_one_episode_capped_samples(captured: list[dict[str, Any]]) -> None:
    mon = _watch_mon()
    mon._loop_thread_id = threading.get_ident()
    mon._last_tick = 0.0
    for i in range(40):  # one long stall, wakes 0.25s apart
        mon._watch_once(2.0 + i * 0.25)
    assert mon.stack_captures == loop_monitor.STACK_MAX_SAMPLES
    mon._last_tick = 100.0  # loop ticked again: new stall re-arms
    mon._watch_once(100.1)
    assert mon.stack_captures == loop_monitor.STACK_MAX_SAMPLES
    mon._watch_once(101.5)
    assert mon.stack_captures == loop_monitor.STACK_MAX_SAMPLES + 1


async def test_watchdog_rate_limited(captured: list[dict[str, Any]]) -> None:
    mon = _watch_mon()
    mon._loop_thread_id = threading.get_ident()
    for i in range(20):  # 20 distinct stalls within one minute
        mon._last_tick = float(i)
        mon._watch_once(i + 2.0)
    assert mon.stack_captures == loop_monitor.STACK_MAX_PER_MIN
    mon._last_tick = 200.0
    mon._watch_once(202.0)  # window passed
    assert mon.stack_captures == loop_monitor.STACK_MAX_PER_MIN + 1


async def test_watchdog_threshold_honoured(captured: list[dict[str, Any]]) -> None:
    mon = _watch_mon(stack_threshold_ms=5000.0)
    mon._loop_thread_id = threading.get_ident()
    mon._last_tick = 0.0
    mon._watch_once(3.0)
    assert mon.stack_captures == 0
    mon._watch_once(5.5)
    assert mon.stack_captures == 1


async def test_watchdog_clean_stop_and_idempotent() -> None:
    mon = _watch_mon()
    mon.start()
    mon.start()
    thread = mon._watchdog
    assert thread is not None and thread.is_alive() and thread.daemon
    await mon.stop()
    assert not thread.is_alive()
    await mon.stop()


async def test_watchdog_survives_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[float] = []

    def boom(self: LoopMonitor, now: float) -> None:
        calls.append(now)
        raise RuntimeError("x")

    monkeypatch.setattr(LoopMonitor, "_watch_once", boom)
    mon = _watch_mon(watchdog_interval_s=0.02)
    mon.start()
    await asyncio.sleep(0.2)
    await mon.stop()
    assert len(calls) >= 3  # kept running after raising


async def test_watchdog_sentry_failure_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a, **k):
        raise RuntimeError("x")

    monkeypatch.setattr(loop_monitor.sentry_sdk.Scope, "capture_event", boom)
    mon = _watch_mon()
    mon._report_stall(1500.0, 1, [{"filename": "a.py", "lineno": 1, "function": "f"}])


# idle selector filter (BACKEND-64S/66S: innermost frame selectors.select = late wake, not a blocker)

_IDLE_FRAMES = [
    {"filename": "/app/.venv/bin/worker", "lineno": 10, "function": "<module>"},
    {"filename": "opennem/tasks/app.py", "lineno": 524, "function": "main"},
    {"filename": "arq/worker.py", "lineno": 313, "function": "run"},
    {"filename": "/usr/local/lib/python3.12/selectors.py", "lineno": 468, "function": "select"},
]


async def test_is_idle_select() -> None:
    assert loop_monitor.is_idle_select(_IDLE_FRAMES)
    assert not loop_monitor.is_idle_select(_IDLE_FRAMES[:-1])
    assert not loop_monitor.is_idle_select([])
    assert not loop_monitor.is_idle_select([{"filename": "opennem/x.py", "lineno": 1, "function": "select"}])


async def test_watchdog_skips_idle_select_real_stack(captured: list[dict[str, Any]]) -> None:
    """A thread parked in selector.select() is sampled but not reported."""
    import selectors
    import socket

    a, b = socket.socketpair()
    sel = selectors.DefaultSelector()
    sel.register(a, selectors.EVENT_READ)
    ready = threading.Event()
    tid: list[int] = []

    def park() -> None:
        tid.append(threading.get_ident())
        ready.set()
        sel.select(timeout=5.0)

    t = threading.Thread(target=park, daemon=True)
    t.start()
    ready.wait(1.0)
    time.sleep(0.2)  # let it enter select
    mon = _watch_mon()
    mon._loop_thread_id = tid[0]
    mon._last_tick = 0.0
    mon._watch_once(2.0)
    b.send(b"x")  # wake it
    t.join(2.0)
    sel.close()
    a.close()
    b.close()
    assert mon.idle_select_skips == 1
    assert mon.stack_captures == 0 and captured == []


async def test_watchdog_idle_select_keeps_budget_for_real_blocker(
    captured: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    mon = _watch_mon()
    mon._loop_thread_id = threading.get_ident()
    mon._last_tick = 0.0
    monkeypatch.setattr(loop_monitor, "extract_frames", lambda frame: list(_IDLE_FRAMES))
    for i in range(10):
        mon._watch_once(2.0 + i * 0.25)
    assert mon.idle_select_skips == 10 and mon.stack_captures == 0 and captured == []
    real = [*_IDLE_FRAMES[:-1], {"filename": "opennem/x.py", "lineno": 1, "function": "blocker"}]
    monkeypatch.setattr(loop_monitor, "extract_frames", lambda frame: list(real))
    mon._watch_once(5.0)  # same stall, now a real blocker: still captured
    assert mon.stack_captures == 1
    assert captured[0]["fingerprint"] == ["event-loop-stall", "opennem/x.py:blocker"]
