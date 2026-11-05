"""Early NEM poll: ingest + aggregate the stamp AEMO lists ~2-3 min before the clock reaches it."""

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from opennem.aggregates import market_summary as ms
from opennem.aggregates import unit_intervals as ui
from opennem.tasks import tasks
from opennem.utils import ingest_latency
from opennem.utils.ingest_latency import IngestTrace
from opennem.utils.nem_early import clamp_end_bound, state

_real_sleep = asyncio.sleep
NOW = datetime(2026, 11, 5, 17, 0)  # last completed interval; T is 17:05
T = datetime(2026, 11, 5, 17, 5)
OLD = datetime(2026, 11, 5, 17, 0)


@pytest.fixture(autouse=True)
def _reset():
    tasks._last_scada_interval = OLD
    yield
    tasks._last_scada_interval = None


# bound logic (pure)


def test_clamp_defaults_to_last_completed() -> None:
    assert clamp_end_bound(None, NOW) == NOW


def test_clamp_allows_exactly_one_interval_ahead() -> None:
    assert clamp_end_bound(T, NOW) == T


def test_clamp_never_more_than_one_interval_ahead() -> None:
    assert clamp_end_bound(T + timedelta(minutes=5), NOW) == T
    assert clamp_end_bound(T + timedelta(hours=3), NOW) == T


def test_clamp_never_before_last_completed() -> None:
    assert clamp_end_bound(NOW - timedelta(minutes=30), NOW) == NOW


def test_clamp_strips_tz() -> None:
    aware = T.replace(tzinfo=tasks._AEST)
    assert clamp_end_bound(aware, NOW.replace(tzinfo=tasks._AEST)) == T


# aggregates take the early bound


def _run_to_now(max_interval: datetime, now: datetime, end_date: datetime | None):
    get_data = AsyncMock(return_value=[])
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    session_cm.__aexit__ = AsyncMock(return_value=False)
    with (
        patch.object(ui, "get_clickhouse_client", MagicMock()),
        patch.object(ui, "execute_async", AsyncMock(return_value=[(max_interval,)])),
        patch.object(ui, "get_last_completed_interval_for_network", lambda **_: now),
        patch.object(ui, "get_write_session", MagicMock(return_value=session_cm)),
        patch.object(ui, "_get_unit_interval_data", get_data),
        patch.object(ui, "_prepare_unit_interval_data", lambda r: list(r)),
        patch.object(ui, "insert_async", AsyncMock()),
        patch.object(ui, "write_agg_rows", AsyncMock()),
    ):
        asyncio.run(ui.run_unit_intervals_aggregate_to_now(end_date=end_date))
    return get_data


def test_unit_intervals_early_bound_includes_future_stamp() -> None:
    get_data = _run_to_now(NOW - timedelta(minutes=5), NOW, end_date=T)
    # CH max 16:55 -> 17:00 and the still-future 17:05 in one run, inclusive
    assert get_data.await_args.args[1:3] == (NOW, T)
    assert get_data.await_args.kwargs == {"inclusive_end": True}


def test_unit_intervals_early_bound_is_clamped() -> None:
    get_data = _run_to_now(NOW - timedelta(minutes=5), NOW, end_date=T + timedelta(minutes=15))
    assert get_data.await_args.args[2] == T


def test_unit_intervals_safety_net_noops_after_early_run() -> None:
    # early run left CH at T; the T+8s cron's clock bound is T: nothing to process
    get_data = _run_to_now(T, T, end_date=None)
    get_data.assert_not_awaited()


def test_market_summary_early_bound() -> None:
    get_data = AsyncMock(return_value=[])
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    session_cm.__aexit__ = AsyncMock(return_value=False)
    with (
        patch.object(ms, "get_last_completed_interval_for_network", lambda **_: NOW),
        patch.object(ms, "get_write_session", MagicMock(return_value=session_cm)),
        patch.object(ms, "_get_market_summary_data", get_data),
        patch.object(ms, "_prepare_market_summary_data", AsyncMock(return_value=[])),
        patch.object(ms, "insert_async", AsyncMock()),
    ):
        asyncio.run(ms.run_market_summary_aggregate_for_last_intervals(12, end_date=T + timedelta(minutes=10)))
    assert get_data.await_args.args[1:3] == (T - timedelta(minutes=60), T)


def test_energy_early_bound() -> None:
    from opennem.workers import energy

    calc = AsyncMock()
    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=MagicMock())
    session_cm.__aexit__ = AsyncMock(return_value=False)
    with (
        patch.object(energy, "get_last_completed_interval_for_network", lambda **_: NOW),
        patch.object(energy, "get_write_session", MagicMock(return_value=session_cm)),
        patch.object(energy, "_calculate_energy_for_interval", calc),
    ):
        asyncio.run(energy.process_energy_last_intervals(num_intervals=12, end_time=T))
    assert calc.await_args.kwargs["end_time"] == T


# trace relative to the stamp


def test_trace_marks_are_relative_to_stamp_negative_before() -> None:
    trace = IngestTrace(T)
    with patch.object(ingest_latency.time, "time", lambda: trace.boundary - 160.0):
        trace.mark("listed")
        trace.mark("listed", "prices")
    with patch.object(ingest_latency.time, "time", lambda: trace.boundary - 120.5):
        trace.mark("ch_aggregate")
    assert trace.marks == {"listed": -160.0, "prices_listed": -160.0, "ch_aggregate": -120.5}


# the poll loop


class Env:
    """Fake AEMO: per-feed newest-listed sequences (last repeats), a fake clock, recorded calls"""

    def __init__(self, scada: list, prices: list) -> None:
        self.clock = [0.0]
        self.listings = {tasks.AEMONNemwebDispatchScada.url: list(scada), tasks.AEMONemwebDispatchIS.url: list(prices)}
        self.calls = dict.fromkeys(self.listings, 0)
        self.crawls: list[tuple[str, dict]] = []
        self.events: list[str] = []

    async def listed(self, url: str):
        seq = self.listings[url]
        i = min(self.calls[url], len(seq) - 1)
        self.calls[url] += 1
        self.clock[0] += 0.1
        if isinstance(seq[i], Exception):
            raise seq[i]
        return seq[i]

    async def crawl(self, crawler, **kwargs):
        self.crawls.append((crawler.name, kwargs))
        if crawler is tasks.AEMONNemwebDispatchScada:
            return SimpleNamespace(inserted_records=5, interval_max=T)
        if crawler is tasks.AEMONemwebDispatchIS:
            return SimpleNamespace(inserted_records=3, interval_max=T)
        return SimpleNamespace(inserted_records=0)

    async def sleep(self, seconds: float) -> None:
        self.clock[0] += seconds
        await _real_sleep(0)  # a real wait lets the other feed's poll run

    def run(self, budget: float = 60.0, pipeline_error: Exception | None = None) -> None:
        async def _energy(**kw):
            self.events.append(f"energy:{kw['end_time']:%H:%M}")

        async def _market(**kw):
            self.events.append(f"market:{kw['end_date']:%H:%M}")

        async def _agg(**kw):
            self.events.append(f"agg:{kw['end_date']:%H:%M}")
            if pipeline_error:
                raise pipeline_error
            return 1

        with (
            patch.object(tasks, "get_newest_listed_interval", AsyncMock(side_effect=self.listed)),
            patch.object(tasks, "run_crawl", AsyncMock(side_effect=self.crawl)),
            patch.object(tasks.asyncio, "sleep", self.sleep),
            patch.object(tasks.time, "monotonic", lambda: self.clock[0]),
            patch.object(tasks, "process_energy_last_intervals", _energy),
            patch.object(tasks, "run_market_summary_aggregate_for_last_intervals", _market),
            patch.object(tasks, "run_unit_intervals_aggregate_to_now", _agg),
        ):
            asyncio.run(tasks.run_nem_early_poll(T, budget_seconds=budget))

    def crawls_of(self, crawler) -> list[dict]:
        return [kw for name, kw in self.crawls if name == crawler.name]


def test_new_files_ingested_once_per_feed_then_pipeline_runs_to_the_future_stamp() -> None:
    env = Env(scada=[OLD, OLD, T], prices=[OLD, T])
    env.run()
    assert env.crawls_of(tasks.AEMONNemwebDispatchScada) == [{"latest": True, "extra_intervals": [T]}]
    assert env.crawls_of(tasks.AEMONemwebDispatchIS) == [{"latest": True, "extra_intervals": [T]}]
    # energy -> market -> CH, all through the still-future 17:05
    assert env.events == ["energy:17:05", "market:17:05", "agg:17:05"]
    assert tasks._last_scada_interval == T
    assert state.aggregated == T
    assert state.prices == T


def test_no_file_means_no_crawl_and_budget_expiry_is_quiet() -> None:
    env = Env(scada=[OLD], prices=[OLD])
    env.run(budget=20.0)
    assert env.crawls == []
    assert env.events == []
    # one request per 2s per feed, none after the budget (the two fake feeds share one clock, so no total-time bound)
    for url, n in env.calls.items():
        assert 5 <= n <= 20 / tasks.NEM_EARLY_POLL_INTERVAL_SECONDS + 2, url
    assert state.aggregated is None


def test_listing_flap_to_older_file_is_noise() -> None:
    env = Env(scada=[OLD, T, OLD, OLD, T], prices=[T])
    env.run()
    # first sight of T ingests and stops polling that feed: the flap back to OLD changes nothing
    assert len(env.crawls_of(tasks.AEMONNemwebDispatchScada)) == 1
    assert env.calls[tasks.AEMONNemwebDispatchScada.url] == 2
    assert state.aggregated == T


def test_listing_error_is_noise_not_a_crawl() -> None:
    env = Env(scada=[RuntimeError("boom"), OLD, T], prices=[T])
    env.run()
    assert len(env.crawls_of(tasks.AEMONNemwebDispatchScada)) == 1
    assert state.aggregated == T


def test_prices_listed_first_does_not_wait_on_scada_listing() -> None:
    env = Env(scada=[OLD, OLD, OLD, T], prices=[T])
    env.run()
    names = [n for n, _ in env.crawls]
    assert names.index(tasks.AEMONemwebDispatchIS.name) < names.index(tasks.AEMONNemwebDispatchScada.name)
    assert state.aggregated == T


def test_prices_never_listed_leaves_pipeline_to_safety_net() -> None:
    env = Env(scada=[T], prices=[OLD])
    env.run(budget=10.0)
    assert len(env.crawls_of(tasks.AEMONNemwebDispatchScada)) == 1
    assert env.events == []
    assert state.aggregated is None
    assert tasks._last_scada_interval == T  # scada is stored, the safety net does not poll for it


def test_scada_never_listed_runs_no_pipeline_even_if_prices_landed() -> None:
    env = Env(scada=[OLD], prices=[T])
    env.run(budget=10.0)
    assert env.events == []
    assert state.aggregated is None


def test_listed_but_nothing_inserted_retries_a_bounded_number_of_times() -> None:
    env = Env(scada=[T], prices=[T])

    async def _empty(crawler, **kwargs):
        env.crawls.append((crawler.name, kwargs))
        return SimpleNamespace(inserted_records=0)

    env.crawl = _empty  # type: ignore[method-assign]
    env.run(budget=600.0)
    assert len(env.crawls_of(tasks.AEMONNemwebDispatchScada)) == tasks.NEM_EARLY_INGEST_MAX_ATTEMPTS
    assert env.events == []


def test_pipeline_failure_leaves_state_unset_for_the_safety_net() -> None:
    env = Env(scada=[T], prices=[T])
    env.run(pipeline_error=RuntimeError("ch down"))
    assert env.events[-1] == "agg:17:05"
    assert state.aggregated is None


def test_cancelled_while_polling_cancels_both_feeds() -> None:
    cancelled: list[str] = []

    async def _listed(url: str):
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            cancelled.append(url)
            raise

    async def _main() -> None:
        task = asyncio.create_task(tasks.run_nem_early_poll(T, budget_seconds=60))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    with patch.object(tasks, "get_newest_listed_interval", _listed):
        asyncio.run(_main())
    assert sorted(cancelled) == sorted([tasks.AEMONNemwebDispatchScada.url, tasks.AEMONemwebDispatchIS.url])


def test_trace_line_reports_both_feeds_relative_to_stamp(caplog) -> None:
    env = Env(scada=[T], prices=[T])
    tasks.logger.addHandler(caplog.handler)
    tasks.logger.setLevel("INFO")
    ingest_latency.logger.addHandler(caplog.handler)
    ingest_latency.logger.setLevel("INFO")
    try:
        env.run()
    finally:
        tasks.logger.removeHandler(caplog.handler)
        ingest_latency.logger.removeHandler(caplog.handler)
    line = next(r.getMessage() for r in caplog.records if r.getMessage().startswith("nem_ingest_latency"))
    assert "listed=" in line and "prices_listed=" in line and "ch_aggregate=" in line
    assert "prices_listed=-" not in line.replace("prices_listed=-0", "")  # real clock is far from T: values exist


# the safety net


def _run_cron(listing=None, hits: dict | None = None):
    hits = hits if hits is not None else {}
    events: list[str] = []

    async def _noop(**_):
        events.append("pipeline")

    async def _agg(**_):
        events.append("pipeline")

    async def _crawl(crawler, **_):
        events.append(f"crawl:{crawler.name}")
        return SimpleNamespace(inserted_records=1)

    async def _warm(ctx):
        events.append("warm")

    async def _export(network):
        events.append(f"export:{network.code}")

    listing_mock = AsyncMock(return_value=listing)
    with (
        patch.object(tasks, "get_last_completed_interval_for_network", lambda **_: T),
        patch.object(tasks, "get_newest_listed_interval", listing_mock),
        patch.object(tasks, "run_crawl", AsyncMock(side_effect=_crawl)),
        patch.object(tasks, "process_energy_last_intervals", _noop),
        patch.object(tasks, "run_market_summary_aggregate_for_last_intervals", _noop),
        patch.object(tasks, "run_unit_intervals_aggregate_to_now", _agg),
        patch.object(tasks, "_enqueue_cache_warm", _warm),
        patch.object(tasks, "run_export_power_latest_for_network", _export),
        patch.object(tasks.asyncio, "sleep", AsyncMock()),
    ):
        asyncio.run(tasks.task_nem_interval_check({}))
    return events, listing_mock


def test_safety_net_skips_to_cache_warm_and_exports_when_early_poll_aggregated() -> None:
    state.aggregated = T
    events, listing = _run_cron()
    assert events == ["warm", f"export:{tasks.NetworkNEM.code}", f"export:{tasks.NetworkAU.code}"]
    listing.assert_not_awaited()  # no polling, no crawl, no second aggregate


def test_safety_net_does_not_poll_for_scada_the_early_poll_stored() -> None:
    tasks._last_scada_interval = T
    state.prices = T
    events, listing = _run_cron(listing=T)
    listing.assert_not_awaited()
    assert not [e for e in events if e.startswith("crawl:")]
    # the early pipeline did not complete (aggregated unset): the safety net still runs it once
    assert events.count("pipeline") == 3
    assert events[-3:] == ["warm", f"export:{tasks.NetworkNEM.code}", f"export:{tasks.NetworkAU.code}"]


def test_safety_net_runs_normally_when_early_poll_did_nothing() -> None:
    tasks._last_scada_interval = OLD
    events, _ = _run_cron(listing=T)
    assert f"crawl:{tasks.AEMONNemwebDispatchScada.name}" in events
    assert events.count("pipeline") == 3
