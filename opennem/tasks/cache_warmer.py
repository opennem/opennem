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

Warm-ahead (#752): a request in slot E (time in (E-5m, E]) keys on date_end=E and, via
`cap_date_end_to_settled_interval`, its content depends only on `min(E, latest)` where `latest` is the newest interval
in ClickHouse. When interval L lands (at L + X, inside slot L+5m) the cycle refreshes slot L+5m; the next slot
L+10m starts at L+5m, and nothing new lands before L+5m+X, so an entry for key L+10m built from the data available
now (latest = L) equals a cold build at the start of that slot. Each cycle therefore refreshes the current slot first,
then pre-builds the next one (cycle phase "ahead"). The post-landing force refresh of the next cycle then overwrites it
with latest = L+5m, exactly as it does for an entry a user cold-built before landing. Late landing: the cold build at
the slot start would also see latest = L-5m, and so does the pre-built entry; the late cycle then refreshes the
now-current slot (already keyed) and pre-builds the one after. TTL for a next-slot entry: `slot_live_ttl`.

Entries are refreshed with `Cache-Control: no-cache` (fastapi-cache recomputes and overwrites): a user who
arrived before the interval finished landing would otherwise leave a stale-by-one-row entry for the warmer
to "hit".

Worker mode (#759): `CACHE_WARM_MODE=worker` builds the same entries inside the worker process instead of asking
the API to do it (the API is 1 vCPU, so the warm load raised live p95). The real route function (the `cached_json`
wrapper around fastapi-cache, so key, TTL, coder and stored bytes are the production ones) is called directly with
a minimal starlette `Request` carrying `Cache-Control: no-cache`, a `Response()`, a ClickHouse client and a user of
the frontend key's tier. See `call_handler` / `run_worker_warm`.
"""

import asyncio
import functools
import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, get_args, get_origin
from urllib.parse import urlencode

import httpx
from pydantic import TypeAdapter

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


# hot-first order (#752): whole NEM then the big regions get warmed before the small ones
REGION_PRIORITY: tuple[str | None, ...] = (None, "NSW1", "VIC1", "QLD1", "SA1", "TAS1")
HOT_REGIONS = frozenset(REGION_PRIORITY[:4])
PHASE_CURRENT = 0
PHASE_AHEAD = 1


@dataclass(frozen=True)
class WarmRequest:
    path: str
    params: tuple[tuple[str, str], ...]
    # sort key, see `priority_key`; not part of identity
    rank: tuple[int, ...] = field(default=(), compare=False)


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


def _naive_local(now: datetime) -> datetime:
    return now.astimezone(NEM_TZ).replace(tzinfo=None) if now.tzinfo is not None else now


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def priority_key(region: str | None, range_idx: int, call_rank: int, phase: int = PHASE_CURRENT) -> tuple[int, ...]:
    """Lower sorts first: current slot before the next one, hot regions, short ranges, then heavy data calls.

    call_rank: 0 = data call on the current window (heavy), 1 = market call, 2 = data call on the prior window.
    """
    region_idx = REGION_PRIORITY.index(region) if region in REGION_PRIORITY else len(REGION_PRIORITY)
    return (phase, 0 if region in HOT_REGIONS else 1, range_idx, region_idx, call_rank)


def _request(
    kind: str,
    metrics: tuple[str, ...],
    region: str | None,
    start: datetime,
    end: datetime,
    interval: str,
    rank: tuple[int, ...] = (),
) -> WarmRequest:
    params: list[tuple[str, str]] = [("metrics", m) for m in metrics]
    params += [("interval", interval), ("date_start", _fmt(start)), ("date_end", _fmt(end))]
    if region:
        params.append(("network_region", region))
    if kind == "data":
        params.append(("secondary_grouping", "fueltech"))
    return WarmRequest(path=f"/v4/{kind}/network/{NETWORK}", params=tuple(params), rank=rank)


def build_requests(
    date_end: datetime,
    *,
    include_30d: bool = False,
    regions: tuple[str | None, ...] = REGIONS,
    phase: int = PHASE_CURRENT,
) -> list[WarmRequest]:
    """All tracker calls for one grid slot: current window for every call, prior window for the data calls.

    Returned in priority order (`priority_key`), so a spent budget drops the least valuable tail.
    """
    ranges = {**RANGES, **(RANGES_30D if include_30d else {})}
    out: list[WarmRequest] = []
    for range_idx, (span, interval) in enumerate(ranges.values()):
        for region in regions:
            for metrics in DATA_CALLS:
                rank = priority_key(region, range_idx, 0, phase)
                out.append(_request("data", metrics, region, date_end - span, date_end, interval, rank))
            for metrics in MARKET_CALLS:
                rank = priority_key(region, range_idx, 1, phase)
                out.append(_request("market", metrics, region, date_end - span, date_end, interval, rank))
            for metrics in DATA_CALLS:  # prior period: now-2span .. now-span
                rank = priority_key(region, range_idx, 2, phase)
                out.append(_request("data", metrics, region, date_end - 2 * span, date_end - span, interval, rank))
    return sorted(out, key=lambda r: r.rank)  # stable: ties keep build order


def build_cycle_requests(grid_end: datetime, *, include_30d: bool = False, ahead: bool = True) -> list[WarmRequest]:
    """Current slot first, then (warm-ahead) the next slot, each in priority order."""
    out = build_requests(grid_end, include_30d=include_30d)
    if ahead:
        out += build_requests(grid_end + GRID, include_30d=include_30d, phase=PHASE_AHEAD)
    return out


def is_worker_mode() -> bool:
    return settings.cache_warm_mode == "worker"


def is_enabled() -> bool:
    if is_worker_mode():
        return bool(
            settings.cache_warm_user_plan or (settings.cache_warm_api_key and settings.cache_warm_api_key.get_secret_value())
        )
    return bool(settings.cache_warm_api_url and settings.cache_warm_api_key and settings.cache_warm_api_key.get_secret_value())


WarmOne = Callable[[WarmRequest, WarmStats], Awaitable[None]]


def _count_response(stats: WarmStats, status_code: int, cache_status: str, label: str) -> None:
    stats.statuses[status_code] = stats.statuses.get(status_code, 0) + 1
    if status_code != 200:
        stats.errors += 1
        logger.warning(f"cache warm non-200: {label} status={status_code}")
        return
    stats.ok += 1
    if cache_status.upper() == "HIT":
        stats.hit += 1
    else:
        stats.miss += 1


async def _warm_one(client: httpx.AsyncClient, req: WarmRequest, stats: WarmStats) -> None:
    stats.attempted += 1
    try:
        resp = await client.get(req.path, params=list(req.params))
    except Exception as e:  # never include the request headers (api key) in logs
        stats.errors += 1
        logger.warning(f"cache warm request failed: {req.path} {type(e).__name__}")
        return
    _count_response(stats, resp.status_code, resp.headers.get(CACHE_STATUS_HEADER, ""), req.path)


async def warm_requests(
    requests: list[WarmRequest],
    client: httpx.AsyncClient | None,
    *,
    concurrency: int,
    budget_seconds: float,
    warm_one: WarmOne | None = None,
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
            req = queue.get_nowait()
            if warm_one is not None:
                await warm_one(req, stats)
            else:
                assert client is not None  # noqa: S101
                await _warm_one(client, req, stats)

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    stats.skipped_budget = queue.qsize()
    stats.elapsed = time.monotonic() - started
    return stats


# --- worker mode (#759) ---

API_CACHE_PREFIX = "api-cache"
_INJECTED_REQUEST = "__fastapi_cache_request"
_INJECTED_RESPONSE = "__fastapi_cache_response"


def _handler_for(path: str) -> Callable[..., Awaitable[Any]]:
    """Route function behind a warm path (/v4/{data|market}/network/{code}); imported lazily (heavy)."""
    kind = path.split("/")[2]
    if kind == "data":
        from opennem.api.data.router import get_network_data as data_handler

        return data_handler
    if kind == "market":
        from opennem.api.market.router import get_network_data as market_handler

        return market_handler
    raise ValueError(f"no handler for warm path {path}")


def _base_type(annotation: Any) -> Any:
    return get_args(annotation)[0] if get_origin(annotation) is Annotated else annotation


def _is_list_type(tp: Any) -> bool:
    return get_origin(tp) is list or any(get_origin(a) is list for a in get_args(tp))


@functools.cache
def _adapter(tp: Any) -> "TypeAdapter[Any]":
    return TypeAdapter(tp)


def build_handler_kwargs(fn: Callable[..., Any], req: WarmRequest, *, client: Any, user: Any) -> dict[str, Any]:
    """Kwargs FastAPI would pass the route for this request: every parameter, defaults filled, query values validated
    with the declared types. The key builder hashes all of them, so the set must match a real request exactly.
    """
    from fastapi.dependencies.utils import get_typed_signature

    sig = get_typed_signature(fn)
    path_params = {"network_code": req.path.rsplit("/", 1)[-1]}
    query: dict[str, list[str]] = {}
    for k, v in req.params:
        query.setdefault(k, []).append(v)
    unknown = set(query) - set(sig.parameters)
    if unknown:
        raise ValueError(f"unknown query params for {req.path}: {sorted(unknown)}")

    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name in (_INJECTED_REQUEST, _INJECTED_RESPONSE):
            continue
        if name == "client":
            kwargs[name] = client
        elif name == "user":
            kwargs[name] = user
        elif name in path_params:
            kwargs[name] = path_params[name]
        elif name in query:
            tp = _base_type(param.annotation)
            kwargs[name] = _adapter(tp).validate_python(query[name] if _is_list_type(tp) else query[name][-1])
        elif param.default is not inspect.Parameter.empty:
            kwargs[name] = param.default
        else:
            raise ValueError(f"missing required param {name} for {req.path}")
    return kwargs


def make_no_cache_request(req: WarmRequest) -> Any:
    """Minimal GET request: `Cache-Control: no-cache` makes fastapi-cache recompute and overwrite the entry."""
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": req.path,
        "query_string": urlencode(list(req.params)).encode(),
        "headers": [(b"cache-control", b"no-cache")],
    }
    return Request(scope)


async def call_handler(req: WarmRequest, *, client: Any, user: Any) -> Any:
    """Run the real route (decorated, so cache key + write are the production ones) for one warm request."""
    from starlette.responses import Response

    fn = _handler_for(req.path)
    kwargs = build_handler_kwargs(fn, req, client=client, user=user)
    kwargs[_INJECTED_REQUEST] = make_no_cache_request(req)
    kwargs[_INJECTED_RESPONSE] = Response()
    return await fn(**kwargs)


async def ensure_worker_cache() -> bool:
    """Init FastAPICache on the API's redis + prefix once per worker process (lazy: only warm cycles pay for it).

    False when the API cache is in-memory (local/test envs): nothing the API reads could be written from here.
    """
    from fastapi_cache import FastAPICache

    try:
        FastAPICache.get_backend()
        return True
    except AssertionError:
        pass
    if not settings.uses_shared_api_cache:
        return False
    from fastapi_cache.backends.redis import RedisBackend
    from redis import asyncio as aioredis

    FastAPICache.init(RedisBackend(aioredis.from_url(str(settings.redis_url))), prefix=API_CACHE_PREFIX)
    return True


async def resolve_warm_user() -> Any:
    """User whose tier the entries are keyed on: explicit plan setting, else the real user behind the warm api key."""
    from opennem.users.plans import OpenNEMPlan
    from opennem.users.schema import OpenNEMRoles, OpenNEMUser

    if settings.cache_warm_user_plan:
        roles = [OpenNEMRoles.anonymous] + ([OpenNEMRoles.admin] if settings.cache_warm_user_admin else [])
        return OpenNEMUser(id="cache-warmer", plan=OpenNEMPlan(settings.cache_warm_user_plan.upper()), roles=roles)
    assert settings.cache_warm_api_key  # noqa: S101
    from opennem.api.security import _resolve_user_from_key

    return await _resolve_user_from_key(settings.cache_warm_api_key.get_secret_value())


def make_worker_warm_one(*, client: Any, user: Any) -> WarmOne:
    async def warm_one(req: WarmRequest, stats: WarmStats) -> None:
        stats.attempted += 1
        try:
            resp = await call_handler(req, client=client, user=user)
        except Exception as e:  # HTTPException (e.g. 404 no data) carries status; never log kwargs (user/key)
            stats.errors += 1
            status = getattr(e, "status_code", None)
            logger.warning(f"cache warm request failed: {req.path} {type(e).__name__}{f' status={status}' if status else ''}")
            return
        _count_response(stats, resp.status_code, resp.headers.get(CACHE_STATUS_HEADER, ""), req.path)

    return warm_one


async def run_worker_warm(requests: list[WarmRequest]) -> WarmStats | None:
    """Build every request's entry in this process. None when the cache backend or user is unavailable."""
    from opennem.db.clickhouse import get_clickhouse_client

    if not await ensure_worker_cache():
        logger.warning("tracker cache warm (worker) skipped: api cache is not redis in this env")
        return None
    try:
        user = await resolve_warm_user()
    except Exception as e:
        logger.warning(f"tracker cache warm (worker) skipped: could not resolve warm user {type(e).__name__}")
        return None
    return await warm_requests(
        requests,
        None,
        concurrency=settings.cache_warm_concurrency,
        budget_seconds=settings.cache_warm_budget_seconds,
        warm_one=make_worker_warm_one(client=get_clickhouse_client(), user=user),
    )


async def flush_non_api_cache(redis: Any) -> int:
    """Startup flush that spares the API response cache (`api-cache:*`); the rest of the db is cleared as flushdb did.

    Deleting in scan batches (unlink) instead of `flushdb` keeps warm entries alive across a worker restart.
    """
    keep = f"{API_CACHE_PREFIX}:".encode()
    deleted = 0
    batch: list[Any] = []
    async for key in redis.scan_iter(count=500):
        raw = key if isinstance(key, bytes) else str(key).encode()
        if raw.startswith(keep):
            continue
        batch.append(key)
        if len(batch) >= 500:
            deleted += await redis.unlink(*batch)
            batch = []
    if batch:
        deleted += await redis.unlink(*batch)
    return deleted


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
        mode = "worker" if is_worker_mode() else "http"
        grid_end = next_grid_end(now or datetime.now(NEM_TZ))
        requests = build_cycle_requests(grid_end, include_30d=settings.cache_warm_include_30d, ahead=settings.cache_warm_ahead)
        # seconds until the slot being refreshed ends (negative = past it); coverage = end offset vs the boundary
        start_offset = (grid_end - _naive_local(now or datetime.now(NEM_TZ))).total_seconds()
        if mode == "worker":
            stats = await run_worker_warm(requests)
            if stats is None:
                return None
        else:
            assert settings.cache_warm_api_url and settings.cache_warm_api_key  # noqa: S101
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
            f"tracker cache warm mode={mode} grid_end={grid_end.isoformat()} ahead={settings.cache_warm_ahead} "
            f"start_to_slot_end={start_offset:.1f}s end_to_slot_end={start_offset - stats.elapsed:.1f}s "
            f"total={stats.total} attempted={stats.attempted} ok={stats.ok} hit={stats.hit} "
            f"miss={stats.miss} errors={stats.errors} skipped_budget={stats.skipped_budget} elapsed={stats.elapsed:.1f}s"
        )
        return stats
    finally:
        _running = False
