"""Live-edge freshness: power-only requests skip the settled cap, and live TTLs align to the next data landing."""

import inspect
from datetime import datetime, timedelta, timezone

import pytest

import opennem.api.data.router as data_router
import opennem.api.intervals as intervals
from opennem.api.intervals import skips_settled_cap
from opennem.api.response_cache import LANDING_OFFSET_SECONDS, landing_aligned_ttl
from opennem.core.metric import Metric

_NEM = timezone(timedelta(hours=10))


def _ttl(minute: int, second: int, micro: int = 0, ceiling: int = 60) -> int:
    return landing_aligned_ttl(ceiling, now=datetime(2026, 11, 5, 16, minute, second, micro, tzinfo=_NEM))


@pytest.mark.parametrize(
    ("minute", "second", "micro", "ttl"),
    [
        (0, 0, 0, 28),  # boundary: this slot's interval lands in 28 s
        (0, 10, 0, 18),
        (0, 22, 0, 6),
        (0, 23, 0, 5),  # 5 s left: floor
        (0, 27, 0, 5),  # 1 s left: floor
        (0, 28, 0, 60),  # landing passed: next is 300 s away, clamp
        (0, 30, 0, 60),
        (2, 30, 0, 60),  # mid cycle
        (3, 59, 0, 60),  # 329 - ... still > 60 (next landing at 5:28 = 89 s)
        (4, 0, 0, 60),  # 88 s
        (4, 30, 0, 58),  # 58 s to 5:28
        (4, 59, 0, 29),
        (4, 59, 500_000, 29),  # 28.5 s left -> ceil
        (4, 59, 999_999, 29),
    ],
)
def test_landing_aligned_ttl(minute: int, second: int, micro: int, ttl: int) -> None:
    assert _ttl(minute, second, micro) == ttl


def test_ttl_never_outlives_landing_by_more_than_floor() -> None:
    base = datetime(2026, 11, 5, 16, 0, 0, tzinfo=_NEM)
    for sec in range(0, 600):
        now = base + timedelta(seconds=sec, milliseconds=3)
        ttl = landing_aligned_ttl(60, now=now)
        assert 5 <= ttl <= 60
        into = (now.minute % 5) * 60 + now.second + now.microsecond / 1e6
        to_landing = LANDING_OFFSET_SECONDS - into if into < LANDING_OFFSET_SECONDS else 300 + LANDING_OFFSET_SECONDS - into
        assert ttl <= max(5, to_landing + 1)  # ceil adds < 1 s


def test_ttl_respects_lower_ceiling() -> None:
    assert _ttl(2, 30, ceiling=30) == 30


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        ([Metric.POWER], True),
        ([Metric.POWER, Metric.POWER], True),
        ([Metric.POWER, Metric.ENERGY], False),
        ([Metric.ENERGY], False),
        ([Metric.EMISSIONS], False),
        ([], False),
    ],
)
def test_skips_settled_cap(metrics: list[Metric], expected: bool) -> None:
    assert skips_settled_cap(metrics) is expected


class _Stop(Exception):
    pass


async def _call_live(monkeypatch: pytest.MonkeyPatch, metrics: list[Metric]) -> list[bool]:
    """Call the unwrapped network route live (no date_end); returns [cap_called]."""
    called: list[bool] = []

    async def fake_cap(**_kw: object) -> datetime:
        called.append(True)
        return datetime(2026, 11, 5, 16, 0)

    def stop(*_a: object, **_k: object) -> None:
        raise _Stop

    monkeypatch.setattr(data_router, "cap_date_end_to_settled_interval", fake_cap)
    monkeypatch.setattr(
        data_router, "validate_date_range", lambda **_k: (datetime(2026, 11, 5, 10, 0), datetime(2026, 11, 5, 16, 5))
    )
    monkeypatch.setattr(data_router, "columnar_supported", lambda *_a, **_k: False)
    monkeypatch.setattr(data_router, "get_timeseries_query", stop)
    route = inspect.unwrap(data_router.get_network_data)
    with pytest.raises(_Stop):
        await route(network_code="NEM", metrics=metrics, interval=data_router.Interval.INTERVAL, client=object())
    return called


@pytest.mark.asyncio
async def test_route_skips_cap_for_power_only(monkeypatch: pytest.MonkeyPatch) -> None:
    assert await _call_live(monkeypatch, [Metric.POWER]) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("metrics", [[Metric.POWER, Metric.ENERGY], [Metric.ENERGY]])
async def test_route_keeps_cap_for_other_metrics(monkeypatch: pytest.MonkeyPatch, metrics: list[Metric]) -> None:
    assert await _call_live(monkeypatch, metrics) == [True]


@pytest.mark.asyncio
async def test_latest_interval_cache_expires_at_landing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A max(interval) fetched just before landing must not be cached past it."""
    intervals._latest_interval_cache.clear()

    async def fake(client, query, params):  # noqa: ANN001, ANN202
        return [[datetime(2026, 11, 5, 15, 55)]]

    monkeypatch.setattr(intervals, "execute_async", fake)
    monkeypatch.setattr(intervals, "landing_aligned_ttl", lambda ceiling: 7)
    from opennem.schema.network import NetworkNEM

    t0 = intervals.time.monotonic()
    await intervals._get_latest_interval(object(), NetworkNEM, "unit_intervals")
    expiry = intervals._latest_interval_cache[("unit_intervals", NetworkNEM.code)][0]
    assert 6 < expiry - t0 < 8
    intervals._latest_interval_cache.clear()
