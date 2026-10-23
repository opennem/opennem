"""
Tracker response-cache warmer (#737).

The browser tracker asks the API for the same ~14 calls per region every time a user switches region or
range, with `date_end` = now (second precision). Cold builds cost 0.3-1.0 s on the 1 vCPU API, so after each
NEM interval lands this worker task replays those calls over HTTP against the API itself, filling the shared
redis response cache before users arrive.

Key alignment (#734): for sub-day intervals the response cache key ceils date_start/date_end to the 5m grid.
A real request at 06:17:30 therefore keys on 06:20:00. The warmer sends `date_end` exactly on the grid point
real requests map to next (`next_grid_end`), and start = end - span (whole-minute spans stay on the grid), so
`tiered_key_builder` produces the same key as any real request in that slot. The key also includes the user
tier (plan + admin flag), so the warmer's api key must belong to the same plan as the frontend's public key.

Entries are refreshed with `Cache-Control: no-cache` (fastapi-cache recomputes and overwrites): a user who
arrived before the interval finished landing would otherwise leave a stale-by-one-row entry for the warmer
to "hit".
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import httpx

from opennem import settings

logger = logging.getLogger("opennem.tasks.cache_warmer")

NEM_TZ = timezone(timedelta(hours=10))
GRID = timedelta(minutes=5)
NETWORK = "NEM"
REQUEST_TIMEOUT_SECONDS = 30.0
CACHE_STATUS_HEADER = "x-fastapi-cache"

REGIONS: tuple[str | None, ...] = ("NSW1", "QLD1", "SA1", "TAS1", "VIC1", None)  # None = whole NEM

# range label -> (span, interval). Order matters: cheapest/most used first so a spent budget drops the tail.
RANGES: dict[str, tuple[timedelta, str]] = {
    "1d": (timedelta(days=1), "5m"),
    "3d": (timedelta(days=3), "5m"),
    "7d": (timedelta(days=7), "5m"),
}
RANGES_30D: dict[str, tuple[timedelta, str]] = {"30d": (timedelta(days=30), "30m")}

# (endpoint, metrics in the order the frontend sends them: the cache key includes list order, grouping)
# data calls carry secondary_grouping=fueltech; the first four also get the prior-period window
DATA_CALLS: tuple[tuple[str, ...], ...] = (
    ("power",),
    ("emissions", "power"),
    ("market_value",),
    ("emissions",),
)
MARKET_CALLS: tuple[tuple[str, ...], ...] = (
    ("price",),
    ("demand",),
    ("generation_renewable", "demand_gross"),
    ("curtailment_solar_utility", "curtailment_wind"),
    ("renewable_proportion",),
    ("flow_imports", "flow_exports"),
)


@dataclass(frozen=True)
class WarmRequest:
    path: str
    params: tuple[tuple[str, str], ...]


@dataclass
class WarmStats:
    total: int = 0
    attempted: int = 0
    ok: int = 0
    hit: int = 0
    miss: int = 0
    errors: int = 0
    skipped_budget: int = 0
    elapsed: float = 0.0
    statuses: dict[int, int] = field(default_factory=dict)


def next_grid_end(now: datetime) -> datetime:
    """Grid point real requests made at `now` (NEM-local) key on: now ceiled to the 5m grid."""
    if now.tzinfo is not None:
        now = now.astimezone(NEM_TZ).replace(tzinfo=None)
    now = now.replace(microsecond=0)
    floored = now.replace(minute=now.minute - now.minute % 5, second=0)
    return floored if floored == now else floored + GRID


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _request(
    kind: str, metrics: tuple[str, ...], region: str | None, start: datetime, end: datetime, interval: str
) -> WarmRequest:
    params: list[tuple[str, str]] = [("metrics", m) for m in metrics]
    params += [("interval", interval), ("date_start", _fmt(start)), ("date_end", _fmt(end))]
    if region:
        params.append(("network_region", region))
    if kind == "data":
        params.append(("secondary_grouping", "fueltech"))
    return WarmRequest(path=f"/v4/{kind}/network/{NETWORK}", params=tuple(params))


def build_requests(
    date_end: datetime, *, include_30d: bool = False, regions: tuple[str | None, ...] = REGIONS
) -> list[WarmRequest]:
    """All tracker calls for one grid slot: current window for every call, prior window for the data calls."""
    ranges = {**RANGES, **(RANGES_30D if include_30d else {})}
    out: list[WarmRequest] = []
    for span, interval in ranges.values():
        for region in regions:
            for metrics in DATA_CALLS:
                out.append(_request("data", metrics, region, date_end - span, date_end, interval))
            for metrics in MARKET_CALLS:
                out.append(_request("market", metrics, region, date_end - span, date_end, interval))
            for metrics in DATA_CALLS:  # prior period: now-2span .. now-span
                out.append(_request("data", metrics, region, date_end - 2 * span, date_end - span, interval))
    return out


def is_enabled() -> bool:
    return bool(settings.cache_warm_api_url and settings.cache_warm_api_key and settings.cache_warm_api_key.get_secret_value())


async def _warm_one(client: httpx.AsyncClient, req: WarmRequest, stats: WarmStats) -> None:
    stats.attempted += 1
    try:
        resp = await client.get(req.path, params=list(req.params))
    except Exception as e:  # never include the request headers (api key) in logs
        stats.errors += 1
        logger.warning(f"cache warm request failed: {req.path} {type(e).__name__}")
        return
    stats.statuses[resp.status_code] = stats.statuses.get(resp.status_code, 0) + 1
    if resp.status_code != 200:
        stats.errors += 1
        logger.warning(f"cache warm non-200: {req.path} status={resp.status_code}")
        return
    stats.ok += 1
    if resp.headers.get(CACHE_STATUS_HEADER, "").upper() == "HIT":
        stats.hit += 1
    else:
        stats.miss += 1


async def warm_requests(
    requests: list[WarmRequest], client: httpx.AsyncClient, *, concurrency: int, budget_seconds: float
) -> WarmStats:
    """Run requests with bounded concurrency; stop starting new ones once the time budget is spent."""
    stats = WarmStats(total=len(requests))
    started = time.monotonic()
    deadline = started + budget_seconds
    queue: asyncio.Queue[WarmRequest] = asyncio.Queue()
    for r in requests:
        queue.put_nowait(r)

    async def worker() -> None:
        while not queue.empty():
            if time.monotonic() >= deadline:
                return
            await _warm_one(client, queue.get_nowait(), stats)

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    stats.skipped_budget = queue.qsize()
    stats.elapsed = time.monotonic() - started
    return stats


_running = False


async def run_cache_warm(now: datetime | None = None) -> WarmStats | None:
    """One warm cycle. None when disabled or the previous cycle is still running."""
    global _running  # noqa: PLW0603
    if not is_enabled():
        return None
    if _running:
        logger.warning("tracker cache warm skipped: previous cycle still running")
        return None
    _running = True
    try:
        assert settings.cache_warm_api_url and settings.cache_warm_api_key  # noqa: S101
        grid_end = next_grid_end(now or datetime.now(NEM_TZ))
        requests = build_requests(grid_end, include_30d=settings.cache_warm_include_30d)
        headers = {
            "Authorization": f"Bearer {settings.cache_warm_api_key.get_secret_value()}",
            "Cache-Control": "no-cache",
            "Accept-Encoding": "gzip",
        }
        async with httpx.AsyncClient(
            base_url=settings.cache_warm_api_url.rstrip("/"), headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        ) as client:
            stats = await warm_requests(
                requests,
                client,
                concurrency=settings.cache_warm_concurrency,
                budget_seconds=settings.cache_warm_budget_seconds,
            )
        logger.info(
            f"tracker cache warm grid_end={grid_end.isoformat()} total={stats.total} attempted={stats.attempted} "
            f"ok={stats.ok} hit={stats.hit} miss={stats.miss} errors={stats.errors} "
            f"skipped_budget={stats.skipped_budget} elapsed={stats.elapsed:.1f}s"
        )
        return stats
    finally:
        _running = False
