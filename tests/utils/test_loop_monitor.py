"""Event loop lag monitor: detection, no false positives, rate limit, shutdown, executor depth."""

import asyncio
import logging
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
