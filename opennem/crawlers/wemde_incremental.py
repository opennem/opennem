"""Incremental fetch and gap healing for the WEMDE dispatch feed (#795).

Each `ReferenceDispatchSolution_<YYYYMMDDHHMM>.json` is one 5-min dispatch interval, the
filename timestamp is the interval itself (AWST naive, +8, verified against facility_scada).
AEMO publishes a file 3 min after its interval (directory listing modified time, all files).

The core is pure (slot grid, missing-slot detection, file selection, batching) so it tests
without IO. The IO wrappers list the directory, read covered slots from facility_scada, fetch
files concurrently and persist.
"""

import asyncio
import logging
import re
import time
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from opennem.clients.wemde import wemde_parse_dispatch
from opennem.core.crawlers.meta import CrawlStatTypes, crawler_set_meta_many
from opennem.core.parsers.dirlisting import get_dirlisting
from opennem.crawlers.wemde import AEMOWEMDEDispatch, persist_wemde_records
from opennem.persistence.schema import BalancingSummarySchema, FacilityScadaSchema
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import get_today_opennem

logger = logging.getLogger("opennem.crawlers.wemde_incremental")

DISPATCH_FILE_RE = re.compile(r"ReferenceDispatchSolution_(\d{12})\.json$")

SLOT = timedelta(minutes=5)
# listing modified time minus filename interval, measured constant across 73 files (Nov 2026)
PUBLISH_LAG = timedelta(minutes=3)
# newest files always re-fetched so dispatch revisions overwrite
REFETCH_NEWEST = 2
# a single incremental run fetches at most this many files, the rest is picked up next run
MAX_FILES_PER_RUN = 24
# files persisted per group after the first (newest) group
PERSIST_GROUP_SIZE = 6
FETCH_CONCURRENCY = 4
# catchup holds more parsed data at once, keep it lower
CATCHUP_FETCH_CONCURRENCY = 3
COVERAGE_WINDOW = timedelta(hours=24)
CATCHUP_BATCH_SIZE = 24
CATCHUP_MAX_FILES = 288
# files are ~30 MB, the default 20s http timeout is too tight when several download at once
DISPATCH_HTTP_TIMEOUT = 90  # int: rnet rejects float timeouts
# poll the listing for the newest file this long before moving on with what is there
POLL_BUDGET_SECONDS = 90.0
POLL_INTERVAL_SECONDS = 5.0


@dataclass(frozen=True)
class DispatchFile:
    interval: datetime
    link: str


# pure core


def floor_slot(dt: datetime) -> datetime:
    """Floor to the 5-min grid, drops seconds."""
    return dt.replace(minute=dt.minute - dt.minute % 5, second=0, microsecond=0)


def parse_dispatch_interval(name: str) -> datetime | None:
    """Interval (naive AWST) from a dispatch filename or link, None if it is not a dispatch file."""
    match = DISPATCH_FILE_RE.search(name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d%H%M")
    except ValueError:
        return None


def dispatch_files_from_links(links: Iterable[str]) -> dict[datetime, DispatchFile]:
    """Index listing links by interval, non dispatch links dropped, duplicates keep the first."""
    files: dict[datetime, DispatchFile] = {}
    for link in links:
        interval = parse_dispatch_interval(link)
        if interval is not None:
            files.setdefault(interval, DispatchFile(interval=interval, link=link))
    return files


def latest_published_slot(now_awst: datetime) -> datetime:
    """Newest interval whose file AEMO should have published by `now_awst` (naive AWST)."""
    return floor_slot(now_awst - PUBLISH_LAG)


def expected_slots(start: datetime, end: datetime) -> list[datetime]:
    """Every 5-min slot from start to end inclusive, both floored to the grid."""
    slot, last = floor_slot(start), floor_slot(end)
    slots: list[datetime] = []
    while slot <= last:
        slots.append(slot)
        slot += SLOT
    return slots


def find_missing_slots(have: Iterable[datetime], start: datetime, end: datetime) -> list[datetime]:
    """Slots in [start, end] with no data, oldest first. Off-grid or out-of-window `have` entries are ignored."""
    covered = set(have)
    return [s for s in expected_slots(start, end) if s not in covered]


def select_incremental(
    available: dict[datetime, DispatchFile],
    missing: Iterable[datetime],
    refetch_newest: int = REFETCH_NEWEST,
    cap: int = MAX_FILES_PER_RUN,
) -> list[DispatchFile]:
    """Files to fetch this run, newest first: the newest `refetch_newest` plus files for missing slots, capped."""
    wanted = set(sorted(available, reverse=True)[:refetch_newest])
    wanted.update(s for s in missing if s in available)
    return [available[s] for s in sorted(wanted, reverse=True)[:cap]]


def plan_catchup(
    available: dict[datetime, DispatchFile],
    missing: Iterable[datetime],
    batch_size: int = CATCHUP_BATCH_SIZE,
    max_files: int = CATCHUP_MAX_FILES,
) -> list[list[DispatchFile]]:
    """Batches (newest first) of files that fill missing slots. Slots with no published file are skipped."""
    slots = sorted({s for s in missing if s in available}, reverse=True)[:max_files]
    files = [available[s] for s in slots]
    return [files[i : i + batch_size] for i in range(0, len(files), batch_size)]


def persist_groups(
    files: Sequence[DispatchFile], first: int = REFETCH_NEWEST, size: int = PERSIST_GROUP_SIZE
) -> list[list[DispatchFile]]:
    """Split newest-first files so the newest `first` persist before the backlog, which follows in groups of `size`."""
    if not files:
        return []
    groups = [list(files[:first])]
    rest = list(files[first:])
    groups.extend(rest[i : i + size] for i in range(0, len(rest), size))
    return groups


def fs_intervals(records: Iterable[FacilityScadaSchema | BalancingSummarySchema]) -> set[datetime]:
    return {r.interval for r in records if isinstance(r, FacilityScadaSchema) and r.interval}


@dataclass
class LatencyTrace:
    """Marks seconds from the 5-min boundary the run started in, logged as one line per cycle."""

    name: str
    start: datetime = field(default_factory=lambda: datetime.now(UTC))
    marks: dict[str, float] = field(default_factory=dict)

    def mark(self, label: str, now: datetime | None = None) -> None:
        self.marks[label] = seconds_from_boundary(self.start, now or datetime.now(UTC))

    def line(self) -> str:
        parts = " ".join(f"{k}={v:.1f}" for k, v in self.marks.items())
        return f"{self.name} {parts}"

    def log(self) -> None:
        logger.info(self.line())


def seconds_from_boundary(start: datetime, at: datetime) -> float:
    """Seconds from the 5-min boundary at or before `start` to `at` (aware datetimes)."""
    return (at - floor_slot(start)).total_seconds()


# io


_COVERED_QUERY = text(
    """
    select distinct fs.interval
    from facility_scada fs
    where fs.network_id = 'WEM'
        and fs.is_forecast is false
        and fs.interval >= :start
        and fs.interval <= :end
    """
)


async def get_covered_slots(start: datetime, end: datetime) -> set[datetime]:
    """Slots with facility_scada rows for WEM in [start, end] (naive AWST)."""
    from opennem.db import get_read_session

    async with get_read_session() as session:
        rows = (await session.execute(_COVERED_QUERY, {"start": start, "end": end})).all()

    return {r[0] for r in rows}


async def list_dispatch_files() -> dict[datetime, DispatchFile]:
    url = AEMOWEMDEDispatch.url
    if not url:
        raise Exception("WEM dispatch crawler has no url")
    listing = await get_dirlisting(url, timezone=NetworkWEM.timezone)
    return dispatch_files_from_links(e.link for e in listing.get_files())


async def poll_for_slot(
    slot: datetime,
    budget: float = POLL_BUDGET_SECONDS,
    interval: float = POLL_INTERVAL_SECONDS,
    lister: Callable[[], Awaitable[dict[datetime, DispatchFile]]] | None = None,
) -> dict[datetime, DispatchFile]:
    """List the directory until the file for `slot` shows up or the budget is spent, returns the last listing."""
    lister = lister or list_dispatch_files
    deadline = time.monotonic() + budget
    while True:
        available = await lister()
        if slot in available or time.monotonic() + interval > deadline:
            if slot not in available:
                logger.warning(f"wem dispatch file for {slot} not published after {budget}s, moving on")
            return available
        await asyncio.sleep(interval)


async def _fetch_one(
    file: DispatchFile, semaphore: asyncio.Semaphore
) -> list[FacilityScadaSchema | BalancingSummarySchema] | None:
    async with semaphore:
        try:
            return await wemde_parse_dispatch(file.link, timeout=DISPATCH_HTTP_TIMEOUT)
        except Exception as e:
            # isolated: one bad or late file must not drop the others
            logger.error(f"Error parsing dispatch file {file.link}: {e}")
            return None


async def fetch_and_persist(files: Sequence[DispatchFile], concurrency: int = FETCH_CONCURRENCY) -> set[datetime]:
    """Fetch and parse files concurrently (newest first order kept), persist, return persisted facility_scada slots."""
    if not files:
        return set()

    semaphore = asyncio.Semaphore(concurrency)
    results = await asyncio.gather(*(_fetch_one(f, semaphore) for f in files))

    records: list[FacilityScadaSchema | BalancingSummarySchema] = []
    for result in results:
        if result:
            records.extend(result)

    if not records:
        return set()

    persisted = await persist_wemde_records(AEMOWEMDEDispatch, records)
    return fs_intervals(persisted)


async def _set_crawl_meta(slots: set[datetime]) -> None:
    if not slots:
        return
    await crawler_set_meta_many(
        AEMOWEMDEDispatch.name,
        {CrawlStatTypes.last_crawled: get_today_opennem(), CrawlStatTypes.latest_interval: max(slots)},
    )


@dataclass
class IncrementalResult:
    files: int = 0
    persisted: set[datetime] = field(default_factory=set)
    missing_before: int = 0


async def run_wem_dispatch_incremental(trace: LatencyTrace | None = None, now_awst: datetime | None = None) -> IncrementalResult:
    """Fetch only the dispatch files not yet in facility_scada plus the newest two, persist newest first.

    Waits (bounded) for the newest expected file, then heals up to MAX_FILES_PER_RUN missing slots in
    the last 24h so short holes close without the catchup task.
    """
    trace = trace or LatencyTrace("wem_ingest_latency")
    now_awst = now_awst or datetime.now(NetworkWEM.get_fixed_offset()).replace(tzinfo=None)
    target = latest_published_slot(now_awst)

    available = await poll_for_slot(target)
    trace.mark("listing")

    if not available:
        raise Exception("No WEM dispatch files in listing")

    newest = max(available)
    have = await get_covered_slots(newest - COVERAGE_WINDOW, newest)
    missing = find_missing_slots(have, newest - COVERAGE_WINDOW, newest)
    files = select_incremental(available, missing)

    result = IncrementalResult(files=len(files), missing_before=len(missing))
    logger.info(f"wem dispatch incremental: {len(files)} files, {len(missing)} missing slots, newest {newest}")

    for i, group in enumerate(persist_groups(files)):
        slots = await fetch_and_persist(group)
        result.persisted |= slots
        if i == 0:
            trace.mark("fetched_persisted_newest")

    await _set_crawl_meta(result.persisted)
    trace.mark("persisted")
    return result


@dataclass
class CatchupResult:
    healed: set[datetime] = field(default_factory=set)
    missing_before: int = 0
    unpublished: int = 0
    stopped_no_progress: bool = False


async def run_wem_catchup(now_awst: datetime | None = None, concurrency: int = CATCHUP_FETCH_CONCURRENCY) -> CatchupResult:
    """Heal missing 5-min slots in the last 24h. Batches run sequentially, stops when a batch heals nothing."""
    now_awst = now_awst or datetime.now(NetworkWEM.get_fixed_offset()).replace(tzinfo=None)
    end = latest_published_slot(now_awst)
    start = end - COVERAGE_WINDOW

    have = await get_covered_slots(start, end)
    missing = find_missing_slots(have, start, end)
    result = CatchupResult(missing_before=len(missing))

    if not missing:
        logger.info("wem catchup: no missing slots")
        return result

    available = await list_dispatch_files()
    result.unpublished = sum(1 for s in missing if s not in available)
    batches = plan_catchup(available, missing)
    logger.info(f"wem catchup: {len(missing)} missing slots, {result.unpublished} not in listing, {len(batches)} batches")

    missing_set = set(missing)
    for batch in batches:
        persisted = await fetch_and_persist(batch, concurrency=concurrency)
        new = (persisted & missing_set) - result.healed
        if not new:
            logger.warning(f"wem catchup: batch of {len(batch)} files healed nothing, stopping")
            result.stopped_no_progress = True
            break
        result.healed |= new

    await _set_crawl_meta(result.healed)
    logger.info(f"wem catchup: healed {len(result.healed)}/{len(missing)} slots")
    return result
