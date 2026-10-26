"""Tracker cache warmer (#737): warm requests must produce the same cache key as real requests."""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import pytest_asyncio
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from pydantic import SecretStr, TypeAdapter

from opennem.api.cache_keys import tiered_key_builder
from opennem.api.data import router as data_router
from opennem.api.market import router as market_router
from opennem.core.grouping import SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval
from opennem.tasks import cache_warmer as cw
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit


def _user(remaining: int = 5) -> OpenNEMUser:
    return OpenNEMUser(
        id="fe",
        plan=OpenNEMPlan.COMMUNITY,
        roles=[OpenNEMRoles.anonymous],
        rate_limit=OpenNEMUserRateLimit(limit=60, remaining=remaining, reset=1_700_000_000_000),
    )


def _fn() -> None: ...


def _kwargs_from_params(params: tuple[tuple[str, str], ...]) -> dict[str, Any]:
    """Parse query params the way FastAPI does for the network routes."""
    d: dict[str, Any] = {
        "network_code": cw.NETWORK,
        "metrics": [TypeAdapter(Metric).validate_python(v) for k, v in params if k == "metrics"],
        "network_region": None,
        "primary_grouping": data_router.PrimaryGrouping.NETWORK,
        "secondary_grouping": None,
    }
    for k, v in params:
        if k == "interval":
            d["interval"] = Interval(v)
        elif k in ("date_start", "date_end"):
            d[k] = datetime.fromisoformat(v)
        elif k == "network_region":
            d[k] = v
        elif k == "secondary_grouping":
            d[k] = SecondaryGrouping(v)
    return d


def _bench_real_request(kind: str, metrics: tuple[str, ...], region: str | None, now: datetime, span: timedelta, interval: str):
    """What the browser/bench2 sends: date_end=now at second precision, date_start=now-span."""
    return cw._request(kind, metrics, region, now - span, now, interval)


def _key(params: tuple[tuple[str, str], ...], kind: str) -> str:
    fn = data_router.get_network_data if kind == "data" else market_router.get_network_data
    kwargs = _kwargs_from_params(params)
    if kind == "market":
        kwargs.pop("secondary_grouping")
    return tiered_key_builder(fn, "ns", args=(), kwargs={**kwargs, "user": _user(), "client": object()})


# --- grid maths ---


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 10, 24, 6, 17, 30), datetime(2026, 10, 24, 6, 20)),
        (datetime(2026, 10, 24, 6, 15, 1), datetime(2026, 10, 24, 6, 20)),
        (datetime(2026, 10, 24, 6, 15, 0), datetime(2026, 10, 24, 6, 15)),
        (datetime(2026, 10, 24, 6, 19, 59, 999_999), datetime(2026, 10, 24, 6, 20)),
        (datetime(2026, 10, 24, 23, 58, 0), datetime(2026, 10, 25, 0, 0)),
    ],
)
def test_next_grid_end(now: datetime, expected: datetime) -> None:
    assert cw.next_grid_end(now) == expected


# --- key equality ---


def test_request_count_default_and_30d() -> None:
    end = datetime(2026, 10, 24, 6, 20)
    # per range per region: 4 data + 6 market + 4 prior = 14; 3 ranges x 6 regions
    assert len(cw.build_requests(end)) == 14 * 6 * 3
    assert len(cw.build_requests(end, include_30d=True)) == 14 * 6 * 4


def test_all_warm_requests_end_on_grid() -> None:
    end = datetime(2026, 10, 24, 6, 20)
    for r in cw.build_requests(end, include_30d=True):
        d = dict(r.params)
        for k in ("date_start", "date_end"):
            t = datetime.fromisoformat(d[k])
            assert t.second == 0 and t.minute % 5 == 0


@pytest.mark.parametrize("second", [0, 1, 17, 30, 59])
@pytest.mark.parametrize("range_label", ["1d", "3d", "7d", "30d"])
def test_warm_key_equals_real_request_key_within_slot(second: int, range_label: str) -> None:
    slot_end = datetime(2026, 10, 24, 6, 20)
    # real request lands anywhere in (06:15:00, 06:20:00]: 06:15:{second} (not on-grid unless second==0 -> 06:15 slot)
    now = datetime(2026, 10, 24, 6, 17, second)
    if second == 0:
        now = datetime(2026, 10, 24, 6, 17, 0)
    assert cw.next_grid_end(now) == slot_end
    warm = {(r.path, r.params): r for r in cw.build_requests(slot_end, include_30d=True)}
    span, interval = {**cw.RANGES, **cw.RANGES_30D}[range_label]
    checked = 0
    for region in cw.REGIONS:
        for metrics in cw.DATA_CALLS:
            for kind, real_span_end in (("data", now), ("data", now - span)):
                real = cw._request(kind, metrics, region, real_span_end - span, real_span_end, interval)
                # prior window (end = now-span) lands on the same slot shifted by span
                warm_end = slot_end if real_span_end == now else slot_end - span
                expect = cw._request(kind, metrics, region, warm_end - span, warm_end, interval)
                assert (expect.path, expect.params) in warm
                assert _key(real.params, kind) == _key(expect.params, kind)
                checked += 1
        for metrics in cw.MARKET_CALLS:
            real = _bench_real_request("market", metrics, region, now, span, interval)
            expect = cw._request("market", metrics, region, slot_end - span, slot_end, interval)
            assert (expect.path, expect.params) in warm
            assert _key(real.params, "market") == _key(expect.params, "market")
            checked += 1
    assert checked == 6 * (8 + 6)


def test_next_slot_key_differs() -> None:
    a = cw._request("market", ("price",), None, datetime(2026, 10, 24, 5, 20), datetime(2026, 10, 24, 6, 20), "5m")
    b = cw._request("market", ("price",), None, datetime(2026, 10, 24, 5, 25), datetime(2026, 10, 24, 6, 25), "5m")
    assert _key(a.params, "market") != _key(b.params, "market")


# --- end to end through the real handlers: a real request after the warm request is a cache HIT ---


@pytest_asyncio.fixture
async def _cache():
    FastAPICache.init(InMemoryBackend(), prefix="test")
    yield
    FastAPICache.reset()


@pytest.mark.asyncio
async def test_real_market_request_hits_warm_entry(monkeypatch: pytest.MonkeyPatch, _cache: None) -> None:
    actual = AsyncMock(return_value=([{"metric": "price"}], True))
    monkeypatch.setattr(market_router, "_actual_timeseries", actual)
    monkeypatch.setattr(market_router, "build_timeseries_response", lambda ts: {"data": ts})

    async def call(params: tuple[tuple[str, str], ...]) -> Any:
        kw = _kwargs_from_params(params)
        kw.pop("secondary_grouping")  # market route has no such param
        return await market_router.get_network_data(**kw, user=_user(), client=object())

    slot_end = datetime(2026, 10, 24, 6, 20)
    warm = cw._request("market", ("price",), "NSW1", slot_end - timedelta(days=1), slot_end, "5m")
    await call(warm.params)
    for sec in (3, 29, 59):
        now = datetime(2026, 10, 24, 6, 19, sec)
        real = cw._request("market", ("price",), "NSW1", now - timedelta(days=1), now, "5m")
        await call(real.params)
    assert actual.call_count == 1


# --- scheduling guard / disabled ---


def _enable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cw.settings, "cache_warm_api_url", "http://api.test", raising=False)
    monkeypatch.setattr(cw.settings, "cache_warm_api_key", SecretStr("k"), raising=False)


@pytest.mark.asyncio
async def test_disabled_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cw.settings, "cache_warm_api_url", None, raising=False)
    monkeypatch.setattr(cw.settings, "cache_warm_api_key", SecretStr("k"), raising=False)
    assert not cw.is_enabled()
    assert await cw.run_cache_warm() is None
    monkeypatch.setattr(cw.settings, "cache_warm_api_url", "http://api.test", raising=False)
    monkeypatch.setattr(cw.settings, "cache_warm_api_key", None, raising=False)
    assert not cw.is_enabled()
    assert await cw.run_cache_warm() is None


@pytest.mark.asyncio
async def test_overlapping_cycle_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(cw, "_running", True)
    assert await cw.run_cache_warm() is None


@pytest.mark.asyncio
async def test_run_counts_and_limits_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(cw.settings, "cache_warm_concurrency", 2, raising=False)
    monkeypatch.setattr(cw.settings, "cache_warm_include_30d", False, raising=False)
    monkeypatch.setattr(cw.settings, "cache_warm_ahead", False, raising=False)
    seen: list[httpx.Request] = []
    inflight = 0
    peak = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal inflight, peak
        inflight += 1
        peak = max(peak, inflight)
        seen.append(request)
        import asyncio

        await asyncio.sleep(0.001)
        inflight -= 1
        return httpx.Response(200, headers={"x-fastapi-cache": "MISS"}, json={})

    real_client = httpx.AsyncClient

    def factory(**kw: Any) -> httpx.AsyncClient:
        return real_client(transport=httpx.MockTransport(handler), **kw)

    monkeypatch.setattr(cw.httpx, "AsyncClient", factory)
    stats = await cw.run_cache_warm(now=datetime(2026, 10, 24, 6, 17, 30))
    assert stats is not None
    assert stats.total == stats.attempted == stats.ok == 252
    assert stats.miss == 252 and stats.errors == 0
    assert peak <= 2
    assert seen[0].headers["cache-control"] == "no-cache"
    assert seen[0].headers["authorization"] == "Bearer k"
    assert cw._running is False


@pytest.mark.asyncio
async def test_budget_stops_new_requests() -> None:
    reqs = cw.build_requests(datetime(2026, 10, 24, 6, 20))
    client = MagicMock()

    async def slow_get(*a: Any, **k: Any) -> httpx.Response:
        import asyncio

        await asyncio.sleep(0.05)
        return httpx.Response(200)

    client.get = slow_get
    stats = await cw.warm_requests(reqs, client, concurrency=2, budget_seconds=0.12)
    assert 0 < stats.attempted < len(reqs)
    assert stats.skipped_budget == len(reqs) - stats.attempted


def test_cache_backend_selection() -> None:
    from opennem.settings_schema import OpennemSettings

    for env, shared in [("local", False), ("test", False), ("development", True), ("dev", True), ("production", True)]:
        assert OpennemSettings(env=env).uses_shared_api_cache is shared


# --- warm-ahead (#752) ---


@pytest.mark.parametrize("second", [0, 1, 17, 30, 59])
@pytest.mark.parametrize("range_label", ["1d", "3d", "7d", "30d"])
def test_warm_ahead_key_equals_real_request_at_next_slot_start(second: int, range_label: str) -> None:
    """Cycle runs in slot 06:20 (grid_end); ahead entries must match a real request a few seconds into slot 06:25."""
    grid_end = datetime(2026, 10, 24, 6, 20)
    next_end = grid_end + cw.GRID
    # real request a few seconds after the slot boundary (06:20:00 + second, second 0 is still slot 06:20)
    now = datetime(2026, 10, 24, 6, 20, second) if second else datetime(2026, 10, 24, 6, 20, 1)
    assert cw.next_grid_end(now) == next_end
    ahead = {(r.path, r.params) for r in cw.build_cycle_requests(grid_end, include_30d=True) if r.rank[0] == cw.PHASE_AHEAD}
    span, interval = {**cw.RANGES, **cw.RANGES_30D}[range_label]
    for region in cw.REGIONS:
        for metrics in cw.DATA_CALLS:
            for end in (now, now - span):  # current and prior window
                real = cw._request("data", metrics, region, end - span, end, interval)
                warm_end = next_end if end == now else next_end - span
                expect = cw._request("data", metrics, region, warm_end - span, warm_end, interval)
                assert (expect.path, expect.params) in ahead
                assert _key(real.params, "data") == _key(expect.params, "data")
        for metrics in cw.MARKET_CALLS:
            real = _bench_real_request("market", metrics, region, now, span, interval)
            expect = cw._request("market", metrics, region, next_end - span, next_end, interval)
            assert (expect.path, expect.params) in ahead
            assert _key(real.params, "market") == _key(expect.params, "market")


def test_cycle_requests_disjoint_and_ahead_optional() -> None:
    end = datetime(2026, 10, 24, 6, 20)
    both = cw.build_cycle_requests(end)
    assert len(both) == 2 * 14 * 6 * 3
    assert len({(r.path, r.params) for r in both}) == len(both)
    assert len(cw.build_cycle_requests(end, ahead=False)) == 14 * 6 * 3
    assert all(r.rank[0] == cw.PHASE_CURRENT for r in cw.build_cycle_requests(end, ahead=False))


def test_priority_order() -> None:
    end = datetime(2026, 10, 24, 6, 20)
    reqs = cw.build_cycle_requests(end)
    ranks = [r.rank for r in reqs]
    assert ranks == sorted(ranks)
    n = len(reqs) // 2
    assert all(r.rank[0] == cw.PHASE_CURRENT for r in reqs[:n])  # current slot fully before the next one

    def region_of(r: cw.WarmRequest) -> str | None:
        return dict(r.params).get("network_region")

    first = reqs[0]
    assert region_of(first) is None and first.path == "/v4/data/network/NEM"  # whole NEM, heavy data, 1d
    assert dict(first.params)["interval"] == "5m"
    cur = reqs[:n]
    # hot regions (NEM, NSW1, VIC1, QLD1) all before SA1/TAS1
    last_hot = max(i for i, r in enumerate(cur) if region_of(r) in (None, "NSW1", "VIC1", "QLD1"))
    first_cold = min(i for i, r in enumerate(cur) if region_of(r) in ("SA1", "TAS1"))
    assert last_hot < first_cold
    # within the hot tier: all 1d before any 3d, before any 7d
    hot = [r for r in cur if region_of(r) in (None, "NSW1", "VIC1", "QLD1")]
    days = [
        (datetime.fromisoformat(dict(r.params)["date_end"]) - datetime.fromisoformat(dict(r.params)["date_start"])).days
        for r in hot
    ]
    assert days == sorted(days)
    # heavy current-window data calls come before market calls for the same region/range
    assert [r.rank[4] for r in hot[:14]] == sorted(r.rank[4] for r in hot[:14])


@pytest.mark.asyncio
async def test_run_with_ahead_warms_both_slots_and_logs_offsets(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _enable(monkeypatch)
    monkeypatch.setattr(cw.settings, "cache_warm_concurrency", 2, raising=False)
    monkeypatch.setattr(cw.settings, "cache_warm_include_30d", False, raising=False)
    monkeypatch.setattr(cw.settings, "cache_warm_ahead", True, raising=False)
    ends: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        ends.append(request.url.params["date_end"])
        return httpx.Response(200, json={})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(cw.httpx, "AsyncClient", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw))
    lg = cw.logger
    lg.addHandler(caplog.handler)
    lg.setLevel("INFO")
    stats = await cw.run_cache_warm(now=datetime(2026, 10, 24, 6, 17, 30))
    assert stats is not None and stats.total == stats.ok == 504
    assert "2026-10-24T06:25:00" in ends
    lg.removeHandler(caplog.handler)
    assert "start_to_slot_end=150.0s" in caplog.text and "end_to_slot_end=" in caplog.text


# --- slot-bounded live TTL for grid-normalised windows ---

_SLOT = datetime(2026, 10, 24, 6, 20)


@pytest.mark.parametrize(
    ("now", "ttl"),
    [
        (datetime(2026, 10, 24, 6, 16, 30), 240),  # 210s left + 30 slack
        (datetime(2026, 10, 24, 6, 15, 1), 330),  # 299s + 30 capped
        (datetime(2026, 10, 24, 6, 19, 58), 60),  # near slot end: floor
        (datetime(2026, 10, 24, 6, 20, 5), 60),  # slot already over
        (datetime(2026, 10, 24, 6, 5, 0), 60),  # 15 min away: short TTL
        (datetime(2026, 10, 24, 6, 10, 0), 60 * 10 + 30),  # next slot, 600s away: full slot + slack, capped 630
        (datetime(2026, 10, 24, 6, 10, 1), 630),  # 599s + 30 = 629 -> bucket 630
        (datetime(2026, 10, 24, 6, 9, 59), 60),  # 601s away: beyond next slot
        (datetime(2026, 10, 24, 6, 12, 0), 510),  # warm-ahead mid-slot: 480 + 30
    ],
)
def test_slot_live_ttl(now: datetime, ttl: int) -> None:
    from opennem.api.response_cache import slot_live_ttl

    got = slot_live_ttl(_SLOT, 60, now=now.replace(tzinfo=cw.NEM_TZ))
    assert got == ttl


def test_slot_live_ttl_never_outlives_slot_by_more_than_slack_plus_bucket() -> None:
    from opennem.api.response_cache import SLOT_TTL_SLACK, slot_live_ttl

    for sec in range(0, 600, 7):  # current slot and the next one (warm-ahead)
        now = datetime(2026, 10, 24, 6, 10, 0) + timedelta(seconds=sec, milliseconds=1)
        got = slot_live_ttl(_SLOT, 60, now=now.replace(tzinfo=cw.NEM_TZ))
        expiry = now + timedelta(seconds=got)
        assert expiry <= _SLOT + timedelta(seconds=max(SLOT_TTL_SLACK + 10, 60))
        if _SLOT - now > timedelta(seconds=30):  # entry (incl. warm-ahead) lives through its whole slot
            assert expiry >= _SLOT  # lives through its whole slot


@pytest.mark.asyncio
async def test_decorator_ttl_and_cache_control_follow_slot(monkeypatch: pytest.MonkeyPatch, _cache: None) -> None:
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    from opennem.api import response_cache as rc

    now = datetime(2026, 10, 24, 6, 16, 30, tzinfo=cw.NEM_TZ)

    class _Clock(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
            return now.astimezone(tz) if tz else now

    monkeypatch.setattr(rc, "datetime", _Clock)
    app = FastAPI()

    @app.get("/w")
    @rc.cached_json(expire=300, live_expire=60, key_builder=tiered_key_builder, return_type=None)
    async def w(
        date_start: datetime | None = None, date_end: datetime | None = None, interval: Interval = Interval.INTERVAL
    ) -> dict:
        return {"ok": 1}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # grid window ending in slot 06:20 -> 06:16:30 + 240s = ~06:20:30
        grid = await c.get("/w?date_start=2026-10-23T06:17:30&date_end=2026-10-24T06:17:30&interval=5m")
        # same window but daily interval is not grid-normalised -> plain live ttl 60
        daily = await c.get("/w?date_start=2026-10-23T06:17:30&date_end=2026-10-24T06:17:30&interval=1d")
        # live (no date_end) -> 60
        live = await c.get("/w")
    assert grid.headers["cache-control"] == "max-age=240"
    assert daily.headers["cache-control"] == "max-age=60"
    assert live.headers["cache-control"] == "max-age=60"
