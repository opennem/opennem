"""WEM dispatch incremental fetch + gap healing (#795)."""

from datetime import UTC, datetime, timedelta

import pytest

from opennem.crawlers import wemde_incremental as wi
from opennem.crawlers.wemde_incremental import DispatchFile
from opennem.persistence.schema import FacilityScadaSchema

BASE = datetime(2026, 11, 5, 14, 0)


def _slot(n: int) -> datetime:
    return BASE + timedelta(minutes=5 * n)


def _link(dt: datetime) -> str:
    return f"https://x/current/ReferenceDispatchSolution_{dt:%Y%m%d%H%M}.json"


def _available(offsets: range | list[int]) -> dict[datetime, DispatchFile]:
    return wi.dispatch_files_from_links(_link(_slot(n)) for n in offsets)


def test_parse_dispatch_interval() -> None:
    assert wi.parse_dispatch_interval("ReferenceDispatchSolution_202611051400.json") == BASE
    assert wi.parse_dispatch_interval("ReferenceDispatchSolution_202611051400.zip") is None
    assert wi.parse_dispatch_interval("ReferenceDispatchSolution_202613451400.json") is None
    assert wi.parse_dispatch_interval("/public/") is None


def test_files_from_links_dedupes_and_drops_non_dispatch() -> None:
    files = wi.dispatch_files_from_links([_link(BASE), _link(BASE) + "?x=1".replace("?x=1", ""), "https://x/other.json"])
    assert list(files) == [BASE]


def test_latest_published_slot_respects_lag() -> None:
    # 14:03 -> file for 14:00 published, 14:02:59 -> only 13:55
    assert wi.latest_published_slot(datetime(2026, 11, 5, 14, 3, 0)) == BASE
    assert wi.latest_published_slot(datetime(2026, 11, 5, 14, 2, 59)) == _slot(-1)
    # crosses midnight
    assert wi.latest_published_slot(datetime(2026, 11, 6, 0, 1)) == datetime(2026, 11, 5, 23, 55)


def test_expected_slots_inclusive_and_floored() -> None:
    slots = wi.expected_slots(_slot(0) + timedelta(minutes=1), _slot(3) + timedelta(minutes=4))
    assert slots == [_slot(0), _slot(1), _slot(2), _slot(3)]
    assert len(wi.expected_slots(BASE - timedelta(hours=24), BASE)) == 289


def test_missing_slots_gap_at_start_middle_end() -> None:
    start, end = _slot(0), _slot(9)
    have = [_slot(i) for i in (2, 3, 4, 5, 6, 7)]
    assert wi.find_missing_slots(have, start, end) == [_slot(0), _slot(1), _slot(8), _slot(9)]


def test_missing_slots_duplicates_and_out_of_window() -> None:
    have = [_slot(1), _slot(1), _slot(1), _slot(-5), _slot(50), _slot(0) + timedelta(minutes=2)]
    assert wi.find_missing_slots(have, _slot(0), _slot(2)) == [_slot(0), _slot(2)]


def test_missing_slots_none_and_all() -> None:
    assert wi.find_missing_slots([_slot(i) for i in range(3)], _slot(0), _slot(2)) == []
    assert wi.find_missing_slots([], _slot(0), _slot(2)) == [_slot(0), _slot(1), _slot(2)]


def test_select_incremental_steady_state_is_newest_two() -> None:
    available = _available(range(-10, 1))
    files = wi.select_incremental(available, missing=[])
    assert [f.interval for f in files] == [_slot(0), _slot(-1)]


def test_select_incremental_adds_missing_newest_first_skips_unpublished() -> None:
    available = _available(range(-10, 1))
    files = wi.select_incremental(available, missing=[_slot(-8), _slot(-5), _slot(-99)])
    assert [f.interval for f in files] == [_slot(0), _slot(-1), _slot(-5), _slot(-8)]


def test_select_incremental_caps_keeping_newest() -> None:
    available = _available(range(-100, 1))
    files = wi.select_incremental(available, missing=list(available), cap=24)
    assert len(files) == 24
    assert files[0].interval == _slot(0)
    assert files[-1].interval == _slot(-23)


def test_select_incremental_empty_listing() -> None:
    assert wi.select_incremental({}, missing=[_slot(0)]) == []


def test_plan_catchup_batches_and_caps() -> None:
    available = _available(range(-399, 1))
    missing = list(available)
    batches = wi.plan_catchup(available, missing, batch_size=24, max_files=288)
    assert sum(len(b) for b in batches) == 288
    assert all(len(b) <= 24 for b in batches)
    assert len(batches) == 12
    assert batches[0][0].interval == _slot(0)
    assert batches[-1][-1].interval == _slot(-287)


def test_plan_catchup_skips_unpublished_and_empty() -> None:
    available = _available([0, -1])
    batches = wi.plan_catchup(available, [_slot(0), _slot(-7)], batch_size=24)
    assert [[f.interval for f in b] for b in batches] == [[_slot(0)]]
    assert wi.plan_catchup(available, []) == []


def test_persist_groups_newest_first() -> None:
    files = list(_available(range(-9, 1)).values())
    files.sort(key=lambda f: f.interval, reverse=True)
    groups = wi.persist_groups(files, first=2, size=4)
    assert [len(g) for g in groups] == [2, 4, 4]
    assert groups[0][0].interval == _slot(0)
    assert wi.persist_groups([]) == []


def test_latency_trace_seconds_from_boundary() -> None:
    start = datetime(2026, 11, 5, 6, 3, 5, tzinfo=UTC)
    trace = wi.LatencyTrace("wem_ingest_latency", start=start)
    trace.mark("start", now=start)
    trace.mark("persisted", now=start + timedelta(seconds=12.5))
    assert trace.marks == {"start": 185.0, "persisted": 197.5}
    assert trace.line() == "wem_ingest_latency start=185.0 persisted=197.5"


# mocked runs


def _record(interval: datetime) -> FacilityScadaSchema:
    return FacilityScadaSchema(network_id="WEM", interval=interval, facility_code="X", generated=1.0, energy=0.1)


class _Fake:
    """Patches the IO edges of wemde_incremental; records which files were fetched and persisted."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, available: dict[datetime, DispatchFile], covered: set[datetime]) -> None:
        self.available = available
        self.covered = covered
        self.fetched: list[datetime] = []
        self.persisted_batches: list[set[datetime]] = []
        self.fail: set[datetime] = set()
        monkeypatch.setattr(wi, "list_dispatch_files", self._list)
        monkeypatch.setattr(wi, "get_covered_slots", self._covered)
        monkeypatch.setattr(wi, "wemde_parse_dispatch", self._parse)
        monkeypatch.setattr(wi, "persist_wemde_records", self._persist)
        monkeypatch.setattr(wi, "_set_crawl_meta", self._meta)

    async def _list(self) -> dict[datetime, DispatchFile]:
        return self.available

    async def _covered(self, start: datetime, end: datetime) -> set[datetime]:
        return {s for s in self.covered if start <= s <= end}

    async def _parse(self, url: str, timeout: float | None = None) -> list[FacilityScadaSchema]:
        interval = wi.parse_dispatch_interval(url)
        assert interval is not None
        if interval in self.fail:
            raise Exception("boom")
        self.fetched.append(interval)
        return [_record(interval)]

    async def _persist(self, crawler: object, data: list[FacilityScadaSchema]) -> list[FacilityScadaSchema]:
        self.persisted_batches.append({r.interval for r in data})
        self.covered |= {r.interval for r in data}
        return data

    async def _meta(self, slots: set[datetime]) -> None:
        return None


@pytest.mark.asyncio
async def test_incremental_steady_state_fetches_two(monkeypatch: pytest.MonkeyPatch) -> None:
    available = _available(range(-300, 1))
    fake = _Fake(monkeypatch, available, covered={_slot(n) for n in range(-300, 0)})
    # the newest is not covered yet, it is a fresh interval
    now = _slot(0) + timedelta(minutes=3, seconds=5)
    trace = wi.LatencyTrace("t")
    result = await wi.run_wem_dispatch_incremental(trace, now_awst=now)
    assert sorted(fake.fetched) == [_slot(-1), _slot(0)]
    assert result.persisted == {_slot(-1), _slot(0)}
    assert fake.persisted_batches == [{_slot(-1), _slot(0)}]
    assert list(trace.marks) == ["listing", "fetched_persisted_newest", "persisted"]


@pytest.mark.asyncio
async def test_incremental_heals_hole_newest_persisted_first(monkeypatch: pytest.MonkeyPatch) -> None:
    available = _available(range(-300, 1))
    hole = {_slot(n) for n in range(-40, -30)}
    fake = _Fake(monkeypatch, available, covered={_slot(n) for n in range(-300, 0)} - hole)
    await wi.run_wem_dispatch_incremental(now_awst=_slot(0) + timedelta(minutes=3))
    assert hole <= set(fake.fetched)
    assert fake.persisted_batches[0] == {_slot(0), _slot(-1)}
    assert len(fake.fetched) == 12


@pytest.mark.asyncio
async def test_incremental_isolates_per_file_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    available = _available(range(-5, 1))
    fake = _Fake(monkeypatch, available, covered={_slot(n) for n in range(-5, 1)})
    fake.fail = {_slot(0)}
    result = await wi.run_wem_dispatch_incremental(now_awst=_slot(0) + timedelta(minutes=3))
    assert result.persisted == {_slot(-1)}


@pytest.mark.asyncio
async def test_poll_waits_for_slot_then_returns(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    async def lister() -> dict[datetime, DispatchFile]:
        calls["n"] += 1
        return _available([0]) if calls["n"] >= 3 else _available([-1])

    sleeps: list[float] = []

    async def fake_sleep(s: float) -> None:
        sleeps.append(s)

    monkeypatch.setattr(wi.asyncio, "sleep", fake_sleep)
    available = await wi.poll_for_slot(_slot(0), budget=90, interval=5, lister=lister)
    assert _slot(0) in available
    assert calls["n"] == 3
    assert sleeps == [5, 5]


@pytest.mark.asyncio
async def test_poll_gives_up_after_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    async def lister() -> dict[datetime, DispatchFile]:
        return _available([-1])

    async def fake_sleep(s: float) -> None:
        return None

    ticks = iter(range(0, 1000, 40))
    monkeypatch.setattr(wi.time, "monotonic", lambda: float(next(ticks)))
    monkeypatch.setattr(wi.asyncio, "sleep", fake_sleep)
    available = await wi.poll_for_slot(_slot(0), budget=90, interval=5, lister=lister)
    assert _slot(0) not in available


@pytest.mark.asyncio
async def test_catchup_heals_gap_in_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    available = _available(range(-400, 1))
    gap = {_slot(n) for n in range(-100, -20)}  # 80 slots
    fake = _Fake(monkeypatch, available, covered={_slot(n) for n in range(-288, 1)} - gap)
    result = await wi.run_wem_catchup(now_awst=_slot(0) + timedelta(minutes=3), concurrency=3)
    assert result.healed == gap
    assert not result.stopped_no_progress
    assert [len(b) for b in fake.persisted_batches] == [24, 24, 24, 8]


@pytest.mark.asyncio
async def test_catchup_stops_when_no_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    available = _available(range(-400, 1))
    gap = {_slot(n) for n in range(-100, -20)}
    fake = _Fake(monkeypatch, available, covered={_slot(n) for n in range(-288, 1)} - gap)
    fake.fail = set(gap)
    result = await wi.run_wem_catchup(now_awst=_slot(0) + timedelta(minutes=3))
    assert result.healed == set()
    assert result.stopped_no_progress
    # one batch tried, the rest skipped
    assert len(fake.fetched) == 0


@pytest.mark.asyncio
async def test_catchup_nothing_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    available = _available(range(-400, 1))
    fake = _Fake(monkeypatch, available, covered={_slot(n) for n in range(-400, 1)})
    result = await wi.run_wem_catchup(now_awst=_slot(0) + timedelta(minutes=3))
    assert result.healed == set() and result.missing_before == 0
    assert fake.fetched == []


@pytest.mark.asyncio
async def test_catchup_missing_slots_not_published_are_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    # files only for the newest hour, 24h grid mostly missing and unpublished
    available = _available(range(-12, 1))
    fake = _Fake(monkeypatch, available, covered=set())
    result = await wi.run_wem_catchup(now_awst=_slot(0) + timedelta(minutes=3))
    assert result.unpublished == result.missing_before - 13
    assert result.healed == set(available)
    assert sorted(fake.fetched) == sorted(available)


def test_dispatch_http_timeout_is_int():
    # rnet.Client rejects float timeouts ("'float' object cannot be interpreted as an integer"), mocks hide it
    from opennem.crawlers.wemde_incremental import DISPATCH_HTTP_TIMEOUT

    assert isinstance(DISPATCH_HTTP_TIMEOUT, int)
