"""
Event loop lag + default-executor depth monitor.

A background task sleeps `interval_s` and measures how late it wakes (monotonic delta minus
interval) = event loop lag. A blocked or starved loop (sync call on the loop, GIL/CPU starvation)
shows up as lag; a healthy loop with a stalled network does not. That distinction is what we could
not make for the 2026-10-07 API stall.

Cost: one timer wakeup per interval (default 0.1s) doing a few float ops, a deque append and a
bounded-window percentile every `report_interval_s` (sorting ~100 floats per 10s). No per-tick IO.
Sentry metrics are buffered/batched by the SDK and emitted once per report interval, not per tick.

Executor depth reads `loop._default_executor._work_queue.qsize()`. That is a PRIVATE attribute of
ThreadPoolExecutor; it is guarded and degrades to None if absent (or if no default executor has
been created yet).
"""

import asyncio
import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Any

import sentry_sdk

from opennem.utils.host import get_hostname

logger = logging.getLogger("opennem.utils.loop_monitor")

# lag above this also sends a Sentry message (fingerprinted) - rare, severe
SEVERE_LAG_MS = 2000.0
WARN_RATE_LIMIT_S = 10.0
REPORT_INTERVAL_S = 10.0
WINDOW_S = 60.0


def _now() -> float:
    """Monotonic clock; module-level so tests can patch it without touching time.monotonic."""
    return time.monotonic()


def get_executor_depth(loop: asyncio.AbstractEventLoop | None = None) -> int | None:
    """Pending items in the loop's default executor queue, or None if not obtainable."""
    try:
        loop = loop or asyncio.get_running_loop()
        executor = getattr(loop, "_default_executor", None)
        if executor is None:
            return None
        return int(executor._work_queue.qsize())  # private attr
    except Exception:
        return None


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(pct / 100 * (len(ordered) - 1)))))
    return ordered[idx]


class LoopMonitor:
    def __init__(
        self,
        service: str,
        interval_s: float = 0.1,
        threshold_ms: float = 250.0,
        window_s: float = WINDOW_S,
        report_interval_s: float = REPORT_INTERVAL_S,
        warn_rate_limit_s: float = WARN_RATE_LIMIT_S,
        severe_ms: float = SEVERE_LAG_MS,
        on_report: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.service = service
        self.interval_s = interval_s
        self.threshold_ms = threshold_ms
        self.report_interval_s = report_interval_s
        self.warn_rate_limit_s = warn_rate_limit_s
        self.severe_ms = severe_ms
        self.hostname = get_hostname()
        self._samples: deque[tuple[float, float]] = deque(maxlen=max(10, int(window_s / interval_s)))
        self._task: asyncio.Task[None] | None = None
        self._last_warn: float | None = None
        self._last_severe: float | None = None
        self._last_report: float = _now()
        self._on_report = on_report
        self.warnings_emitted = 0

    # stats

    def stats(self) -> dict[str, Any]:
        lags = [lag for _, lag in self._samples]
        return {
            "lag_max_ms": max(lags) if lags else 0.0,
            "lag_p99_ms": _percentile(lags, 99),
            "samples": len(lags),
            "executor_depth": get_executor_depth(),
            "threads": threading.active_count(),
        }

    # lifecycle

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.get_running_loop().create_task(self._run(), name="loop-monitor")
            logger.info(f"Loop monitor started ({self.service}): interval={self.interval_s}s threshold={self.threshold_ms}ms")

    async def stop(self) -> None:
        task, self._task = self._task, None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.debug("loop monitor stop error", exc_info=True)

    # internals

    async def _run(self) -> None:
        try:
            while True:
                before = _now()
                await asyncio.sleep(self.interval_s)
                after = _now()
                self._tick(max(0.0, after - before - self.interval_s) * 1000.0, after)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("loop monitor crashed")

    def _tick(self, lag_ms: float, now: float) -> None:
        """Record one sample and fire alerts/reports. Never raises."""
        try:
            self._samples.append((now, lag_ms))
            if lag_ms >= self.threshold_ms:
                self._on_lag(lag_ms, now)
            if now - self._last_report >= self.report_interval_s:
                self._last_report = now
                self._report()
        except Exception:
            logger.debug("loop monitor tick error", exc_info=True)

    def _on_lag(self, lag_ms: float, now: float) -> None:
        if self._last_warn is not None and now - self._last_warn < self.warn_rate_limit_s:
            return
        self._last_warn = now
        self.warnings_emitted += 1
        depth = get_executor_depth()
        threads = threading.active_count()
        logger.warning(
            f"event loop lag {lag_ms:.0f}ms service={self.service} host={self.hostname} executor_depth={depth} threads={threads}"
        )
        data = {"lag_ms": round(lag_ms), "executor_depth": depth, "threads": threads, "host": self.hostname}
        sentry_sdk.add_breadcrumb(category="event-loop-lag", message="event loop lag", level="warning", data=data)
        if lag_ms >= self.severe_ms and (self._last_severe is None or now - self._last_severe >= 60.0):
            self._last_severe = now
            with sentry_sdk.new_scope() as scope:
                scope.fingerprint = ["event-loop-lag"]
                scope.set_tag("service", self.service)
                scope.set_tag("hostname", self.hostname)
                scope.set_tag("lag_ms", str(round(lag_ms)))
                scope.set_tag("executor_depth", str(depth))
                scope.capture_message(f"event loop lag {lag_ms:.0f}ms", level="warning")

    def _report(self) -> None:
        s = self.stats()
        attrs = {"service": self.service, "hostname": self.hostname}
        sentry_sdk.metrics.gauge("event_loop.lag_max", s["lag_max_ms"], unit="millisecond", attributes=attrs)
        sentry_sdk.metrics.gauge("event_loop.lag_p99", s["lag_p99_ms"], unit="millisecond", attributes=attrs)
        sentry_sdk.metrics.gauge("event_loop.threads", float(s["threads"]), attributes=attrs)
        if s["executor_depth"] is not None:
            sentry_sdk.metrics.gauge("event_loop.executor_depth", float(s["executor_depth"]), attributes=attrs)
        if self._on_report:
            self._on_report(s)


_monitor: LoopMonitor | None = None


def start_loop_monitor(service: str) -> LoopMonitor | None:
    """Start the global monitor from settings. Returns None if disabled or on any failure."""
    global _monitor
    try:
        from opennem import settings

        if not settings.loop_monitor_enabled:
            return None
        _monitor = LoopMonitor(
            service=service, interval_s=settings.loop_monitor_interval_s, threshold_ms=settings.loop_monitor_threshold_ms
        )
        _monitor.start()
        return _monitor
    except Exception:
        logger.exception("could not start loop monitor")
        return None


async def stop_loop_monitor() -> None:
    global _monitor
    monitor, _monitor = _monitor, None
    if monitor:
        await monitor.stop()
