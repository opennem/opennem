"""Early NEM ingest: AEMO lists the file stamped T about 2-3 minutes BEFORE T, so the pipeline can run ahead of the clock.

Pure helpers + in-process state shared by the early poll cron and the T+8s safety-net cron. No heavy imports so the
aggregates can use the bound clamp.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

NEM_INTERVAL = timedelta(minutes=5)


def next_stamp(last_completed: datetime) -> datetime:
    """The next dispatch stamp after the wall clock's last completed interval"""
    return last_completed + NEM_INTERVAL


def clamp_end_bound(requested: datetime | None, last_completed: datetime) -> datetime:
    """End bound for the aggregates.

    Default is the wall clock's last completed interval. An early run may ask for the stamp that is still in the
    future, but never more than ONE interval ahead of the clock, and never before the last completed interval.
    """
    last_completed = last_completed.replace(tzinfo=None)
    if requested is None:
        return last_completed
    requested = requested.replace(tzinfo=None)
    return max(last_completed, min(requested, last_completed + NEM_INTERVAL))


@dataclass
class EarlyState:
    """Newest stamps this process has handled. None = unknown, so the safety net does the work"""

    prices: datetime | None = None  # DispatchIS stored to PG
    aggregated: datetime | None = None  # energy + market_summary + unit_intervals (CH) done through this stamp

    def reset(self) -> None:
        self.prices = self.aggregated = None

    def prices_landed(self, stamp: datetime) -> bool:
        return self.prices is not None and self.prices >= stamp

    def aggregated_through(self, stamp: datetime) -> bool:
        return self.aggregated is not None and self.aggregated >= stamp


state = EarlyState()

_locks: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Lock]] = {}


def get_lock(name: str) -> asyncio.Lock:
    """Named in-process lock: `scada` / `prices` serialise the crawl of a feed, `pipeline` the energy/market/aggregate
    section, so the early run and the T+8s safety net never overlap.

    Rebuilt when the running loop changes (tests call asyncio.run repeatedly; a Lock binds to its first loop).
    """
    loop = asyncio.get_running_loop()
    entry = _locks.get(name)
    if entry is None or entry[0] is not loop:
        entry = _locks[name] = (loop, asyncio.Lock())
    return entry[1]
