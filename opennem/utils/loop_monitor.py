"""
Event loop lag + default-executor depth monitor.

A background task sleeps `interval_s` and measures how late it wakes (monotonic delta minus
interval) = event loop lag. A blocked or starved loop (sync call on the loop, GIL/CPU starvation)
shows up as lag; a healthy loop with a stalled network does not. That distinction is what we could
not make for the 2026-10-07 API stall.

Cost: one timer wakeup per interval (default 0.1s) doing a few float ops, a deque append and a
bounded-window percentile every `report_interval_s` (sorting ~100 floats per 10s). No per-tick IO.
Sentry metrics are buffered/batched by the SDK and emitted once per report interval, not per tick.

Stall watchdog: a daemon thread wakes every 250ms and compares now to the loop ticker's last tick. Only when the
loop has been silent past `stack_threshold_ms` does it read the loop thread's current frame via
sys._current_frames() and report the (trimmed, locals-free) stack: up to 3 samples per stall, <= 6 per minute.
Healthy cost: one Event.wait wake + a float compare per 250ms.

Executor depth reads `loop._default_executor._work_queue.qsize()`. That is a PRIVATE attribute of
ThreadPoolExecutor; it is guarded and degrades to None if absent (or if no default executor has
been created yet).
"""

import asyncio
import logging
import sys
import sysconfig
import threading
import time
import traceback
from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

import sentry_sdk

from opennem.utils.host import get_hostname

if TYPE_CHECKING:
    from sentry_sdk._types import Event

logger = logging.getLogger("opennem.utils.loop_monitor")

# lag above this also sends a Sentry message (fingerprinted) - rare, severe
SEVERE_LAG_MS = 2000.0
WARN_RATE_LIMIT_S = 10.0
REPORT_INTERVAL_S = 10.0
WINDOW_S = 60.0

# stall watchdog (thread): wakes every WATCHDOG_INTERVAL_S, does nothing unless the loop has not ticked
WATCHDOG_INTERVAL_S = 0.25
STACK_RESAMPLE_S = 1.0
STACK_MAX_SAMPLES = 3
STACK_MAX_PER_MIN = 6
STACK_MAX_FRAMES = 15
_STDLIB_DIRS = tuple({p for k in ("stdlib", "platstdlib") if (p := sysconfig.get_paths().get(k))})


def _now() -> float:
    """Monotonic clock; module-level so tests can patch it without touching time.monotonic."""
    return time.monotonic()


def _short_path(filename: str) -> str:
    """Trim to `opennem/...` or the site-packages-relative path so no home dirs leak."""
    if "/site-packages/" in filename:
        return filename.rsplit("/site-packages/", 1)[1]
    idx = filename.rfind("/opennem/")
    return filename[idx + 1 :] if idx >= 0 else filename


def _is_stdlib(filename: str) -> bool:
    return filename.startswith(_STDLIB_DIRS) and "site-packages" not in filename


def extract_frames(frame: Any, max_frames: int = STACK_MAX_FRAMES) -> list[dict[str, Any]]:
    """Oldest-first frames (Sentry order) minus stdlib/asyncio plumbing; innermost frame always kept. No locals."""
    summary = traceback.extract_stack(frame)
    out: list[dict[str, Any]] = []
    for i, fs in enumerate(summary):
        if _is_stdlib(fs.filename) and i != len(summary) - 1:
            continue
        out.append({"filename": _short_path(fs.filename), "lineno": fs.lineno, "function": fs.name})
    return out[-max_frames:]


def format_frames(frames: list[dict[str, Any]]) -> str:
    return "\n".join(f"{f['filename']}:{f['lineno']} {f['function']}" for f in frames)


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
        stack_threshold_ms: float = 1000.0,
        watchdog_interval_s: float = WATCHDOG_INTERVAL_S,
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
        # stall watchdog
        self.stack_threshold_ms = stack_threshold_ms
        self.watchdog_interval_s = watchdog_interval_s
        self._last_tick: float = _now()
        self._loop_thread_id: int | None = None
        self._watchdog: threading.Thread | None = None
        self._watchdog_stop = threading.Event()
        self._episode_tick: float | None = None
        self._episode_samples = 0
        self._episode_last_sample = 0.0
        self._capture_times: deque[float] = deque()
        self.stack_captures = 0

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
            self._last_tick = _now()
            self._loop_thread_id = threading.get_ident()
            self._start_watchdog()
            logger.info(f"Loop monitor started ({self.service}): interval={self.interval_s}s threshold={self.threshold_ms}ms")

    async def stop(self) -> None:
        task, self._task = self._task, None
        self._stop_watchdog()
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.debug("loop monitor stop error", exc_info=True)

    # stall watchdog

    def _start_watchdog(self) -> None:
        if self._watchdog is not None and self._watchdog.is_alive():
            return
        self._watchdog_stop.clear()
        self._watchdog = threading.Thread(target=self._watchdog_run, name="loop-stall-watchdog", daemon=True)
        self._watchdog.start()

    def _stop_watchdog(self) -> None:
        thread, self._watchdog = self._watchdog, None
        self._watchdog_stop.set()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

    def _watchdog_run(self) -> None:
        while not self._watchdog_stop.wait(self.watchdog_interval_s):
            try:
                self._watch_once(_now())
            except Exception:
                logger.debug("loop stall watchdog error", exc_info=True)

    def _watch_once(self, now: float) -> None:
        """One watchdog wake: capture the loop thread's stack if it has been stalled past the threshold."""
        last = self._last_tick
        stalled_ms = (now - last) * 1000.0
        if stalled_ms < self.stack_threshold_ms:
            self._episode_tick = None  # loop ticked (or never stalled): re-arm
            return
        if self._episode_tick != last:
            self._episode_tick = last
            self._episode_samples = 0
        if self._episode_samples >= STACK_MAX_SAMPLES:
            return
        if self._episode_samples > 0 and now - self._episode_last_sample < STACK_RESAMPLE_S:
            return
        while self._capture_times and now - self._capture_times[0] >= 60.0:
            self._capture_times.popleft()
        if len(self._capture_times) >= STACK_MAX_PER_MIN:
            return
        frame = sys._current_frames().get(self._loop_thread_id) if self._loop_thread_id is not None else None
        if frame is None:
            return
        frames = extract_frames(frame)
        del frame
        self._episode_samples += 1
        self._episode_last_sample = now
        self._capture_times.append(now)
        self.stack_captures += 1
        self._report_stall(stalled_ms, self._episode_samples, frames)

    def _report_stall(self, stalled_ms: float, sample_n: int, frames: list[dict[str, Any]]) -> None:
        if not frames:
            return
        stack = format_frames(frames[::-1])  # innermost first
        logger.warning(
            f"event loop stalled {stalled_ms:.0f}ms sample={sample_n} service={self.service} host={self.hostname} "
            f"blocking stack (innermost first):\n{stack}"
        )
        try:
            top = frames[-1]
            event: dict[str, Any] = {
                "level": "warning",
                "message": f"event loop stalled {stalled_ms:.0f}ms at {top['function']}",
                "fingerprint": ["event-loop-stall", f"{top['filename']}:{top['function']}"],
                "exception": {
                    "values": [
                        {
                            "type": "EventLoopStall",
                            "value": f"event loop blocked {stalled_ms:.0f}ms",
                            "stacktrace": {"frames": [{**f, "in_app": "site-packages" not in f["filename"]} for f in frames]},
                        }
                    ]
                },
                "extra": {"stack": stack},
            }
            with sentry_sdk.new_scope() as scope:
                scope.set_tag("service", self.service)
                scope.set_tag("hostname", self.hostname)
                scope.set_tag("stall_ms", str(round(stalled_ms)))
                scope.set_tag("sample_n", str(sample_n))
                scope.capture_event(cast("Event", cast(object, event)))
        except Exception:
            logger.debug("loop stall sentry capture failed", exc_info=True)

    # internals

    async def _run(self) -> None:
        try:
            while True:
                before = _now()
                await asyncio.sleep(self.interval_s)
                after = _now()
                self._last_tick = after
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
            service=service,
            interval_s=settings.loop_monitor_interval_s,
            threshold_ms=settings.loop_monitor_threshold_ms,
            stack_threshold_ms=settings.loop_monitor_stack_threshold_ms,
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
