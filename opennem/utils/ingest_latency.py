"""Per-cycle ingest latency trace for the NEM SCADA poll.

One `IngestTrace` is active per `task_nem_interval_check` / `task_nem_early_poll` run (contextvar, so the crawl code
can mark stages without plumbing). Every time is seconds relative to the 5 minute dispatch stamp T the run is for:
negative = before T (the early poll), positive = after. Prices (DispatchIS) stages carry a `prices_` prefix.
"""

import logging
import time
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("opennem.pipelines.nem")

NEM_INTERVAL_SECONDS = 300
# nemweb CSV `C,` header times are AEST (UTC+10, no DST)
_NEM_TZ = timezone(timedelta(hours=10))
# the file for the interval ending at the boundary is generated ~5 min before it (dispatch run time), not at publish
_GENERATED_MIN, _GENERATED_MAX = -330.0, 240.0


class IngestTrace:
    """Stage timestamps (first mark wins) relative to the 5 min boundary"""

    def __init__(self, stamp: datetime | None = None) -> None:
        """stamp: the dispatch stamp T (naive AEST) this run is for. Default: the wall clock's last 5 minute boundary"""
        now = time.time()
        if stamp is not None:
            self.boundary = stamp.replace(tzinfo=_NEM_TZ).timestamp()
        else:
            self.boundary = now - (now % NEM_INTERVAL_SECONDS)
        self.marks: dict[str, float] = {}
        self.file_generated: float | None = None
        self.polls = 0

    def mark(self, stage: str, feed: str | None = None) -> None:
        key = f"{feed}_{stage}" if feed else stage
        self.marks.setdefault(key, round(time.time() - self.boundary, 2))

    def set_file_generated(self, csv_content: bytes) -> None:
        """Parse the AEMO generation time from the CSV `C,` header row (already in memory, no extra work)"""
        if self.file_generated is not None:
            return
        try:
            fields = csv_content[:300].decode("utf-8", errors="ignore").split("\n", 1)[0].split(",")
            generated = datetime.strptime(f"{fields[5]} {fields[6]}", "%Y/%m/%d %H:%M:%S").replace(tzinfo=_NEM_TZ)
        except (IndexError, ValueError):
            return
        rel = generated.timestamp() - self.boundary
        if _GENERATED_MIN <= rel <= _GENERATED_MAX:
            self.file_generated = round(rel, 2)

    def log(self) -> None:
        stages = (
            "cron_start",
            "first_poll",
            "listed",
            "downloaded",
            "parsed",
            "pg_stored",
            "prices_listed",
            "prices_downloaded",
            "prices_pg_stored",
            "ch_aggregate",
        )
        parts = [f"{s}={self.marks.get(s, '-')}" for s in stages]
        parts.append(f"file_generated={self.file_generated if self.file_generated is not None else '-'}")
        parts.append(f"polls={self.polls}")
        logger.info("nem_ingest_latency " + " ".join(parts))


_current_trace: ContextVar[IngestTrace | None] = ContextVar("nem_ingest_trace", default=None)


def start_trace(stamp: datetime | None = None) -> IngestTrace:
    trace = IngestTrace(stamp)
    _current_trace.set(trace)
    return trace


def current_trace() -> IngestTrace | None:
    return _current_trace.get()
