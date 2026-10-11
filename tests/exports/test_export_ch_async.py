"""Export-path ClickHouse reads must run off the event loop and stay byte-identical.

Characterization: fixture rows -> exported JSON compared with a golden captured
from the sync-call implementation (regen: UPDATE_GOLDEN=1). Loop-liveness: a
blocking client.execute must not stall a concurrent ticker. Concurrency: two
concurrent reads never re-enter one client (clickhouse-driver clients are not
safe for concurrent queries on a single connection).
"""

import asyncio
import json
import os
import re
import threading
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from opennem.api.export import controllers as export_controllers
from opennem.controllers import energy as energy_controller
from opennem.controllers.output import flows as flows_controller
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.time import get_interval
from opennem.db.clickhouse import client as ch_client_module
from opennem.schema.network import NetworkNEM

GOLDEN = Path(__file__).parent.parent / "fixtures" / "export_ch_async_golden.json"
_T0 = datetime(2026, 10, 1, 0, 0)
_N = 12


def _norm(js: str) -> str:
    """created_at is wall-clock; everything else must be byte-identical."""
    return re.sub(r'"created_at":"[^"]*"', '"created_at":"X"', js)


def _times(step_min: int = 5) -> list[datetime]:
    return [_T0 + timedelta(minutes=step_min * i) for i in range(_N)]


def _series(interval: str = "5m") -> OpennemExportSeries:
    return OpennemExportSeries(
        start=_T0,
        end=_T0 + timedelta(minutes=5 * (_N - 1)),
        network=NetworkNEM,
        interval=get_interval(interval),
        period=None,
    )


class FakeClient:
    """Non-reentrant fake: raises if two queries overlap on one instance."""

    def __init__(self, rows_for: Callable[[str], list[tuple]], delay: float = 0.0) -> None:
        self._rows_for = rows_for
        self._delay = delay
        self._busy = False
        self._lock = threading.Lock()
        self.reentered = False
        self.threads: set[int] = set()

    def execute(self, query: str, params: Any = None, **kwargs: Any) -> list[tuple]:
        with self._lock:
            if self._busy:
                self.reentered = True
                raise RuntimeError("Simultaneous queries on single connection")
            self._busy = True
        try:
            self.threads.add(threading.get_ident())
            if self._delay:
                time.sleep(self._delay)
            return self._rows_for(query)
        finally:
            self._busy = False


@pytest.fixture
def install_client(monkeypatch: pytest.MonkeyPatch) -> Callable[..., FakeClient]:
    """Patch every place a ClickHouse client is obtained; one fake per thread like the real thread-local."""

    def _install(rows_for: Callable[[str], list[tuple]], delay: float = 0.0) -> FakeClient:
        local = threading.local()
        made: list[FakeClient] = []

        def _get(timeout: int = 10) -> FakeClient:
            c = getattr(local, "c", None)
            if c is None:
                c = FakeClient(rows_for, delay)
                local.c = c
                made.append(c)
            return c

        monkeypatch.setattr(ch_client_module, "get_clickhouse_client", _get)
        for mod in (export_controllers, flows_controller, energy_controller):
            monkeypatch.setattr(mod, "get_clickhouse_client", _get, raising=False)
        monkeypatch.setattr(ch_client_module.settings, "clickhouse_query_max_memory_usage", 0, raising=False)

        class _View:
            @property
            def reentered(self) -> bool:
                return any(c.reentered for c in made)

            @property
            def threads(self) -> set[int]:
                return set().union(*(c.threads for c in made)) if made else set()

        return _View()  # type: ignore[return-value]

    return _install


def _flow_rows(_: str) -> list[tuple]:
    return [
        (t, "NSW1", 10.0 + i, 20.0 + i, 1.5 * i, 2.5 * i, 100.0 + i, 200.0 + i, 0.1 * i, 0.2 * i) for i, t in enumerate(_times())
    ]


def _energy_rows(_: str) -> list[tuple]:
    return [
        (t, ft, 1.0 + i + j, 50.0 + i, 3.0 + j)
        for i, t in enumerate(_times())
        for j, ft in enumerate(["coal_black", "solar_utility"])
    ]


def _demand_rows(_: str) -> list[tuple]:
    return [(t, "NSW1", "NSW1", 5.0 + i, 500.0 + i) for i, t in enumerate(_times())]


def _curtail_rows(_: str) -> list[tuple]:
    return [(t, "NSW1", "NSW1", 0.0, 1.0 + i, 2.0 + i) for i, t in enumerate(_times())]


def _power_rows(q: str) -> list[tuple]:
    # fueltech: (interval, fueltech, power, emissions, ef); price/demand/curtailment: 9 cols
    if "fueltech" in q.lower() and "price" not in q.lower():
        return [
            (t, ft, 100.0 + i + j, 10.0 + i, 0.9)
            for i, t in enumerate(_times())
            for j, ft in enumerate(["coal_black", "gas_ccgt"])
        ]
    return [(t, "NSW1", None, 60.0 + i, 7000.0 + i, None, None, 0.5 * i, 0.25 * i) for i, t in enumerate(_times())]


class _Res:
    def fetchall(self) -> list[tuple]:
        return [(t, "solar_rooftop", 3.0 + i) for i, t in enumerate(_times())]


class _Conn:
    async def execute(self, *_: Any, **__: Any) -> _Res:
        return _Res()


class _Engine:
    @asynccontextmanager
    async def begin(self):  # noqa: ANN202
        yield _Conn()


def _patch_pg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(export_controllers, "db_connect", lambda *a, **k: _Engine())


async def _power_week() -> str:
    ds, _ = await export_controllers.power_week(_series(), "NSW1", [NetworkNEM])
    assert ds is not None
    return ds.model_dump_json(exclude_unset=True)


async def _flows() -> str:
    ds = await flows_controller.power_flows_per_interval(_series(), "NSW1")
    assert ds is not None
    return ds.model_dump_json(exclude_unset=True)


async def _energy() -> str:
    ds = await energy_controller.energy_fueltech_daily(NetworkNEM, _series("1d"), "NSW1")
    assert ds is not None
    return ds.model_dump_json(exclude_unset=True)


async def _demand() -> str:
    ds = await export_controllers.demand_network_region_daily(_series("1d"), "NSW1", [NetworkNEM])
    assert ds is not None
    return ds.model_dump_json(exclude_unset=True)


async def _curtailment() -> str:
    ds = await export_controllers.curtailment_network_region_daily(_series("1d"), "NSW1", [NetworkNEM])
    assert ds is not None
    return ds.model_dump_json(exclude_unset=True)


async def _interconnector() -> str:
    ds = await export_controllers.energy_interconnector_flows_and_emissions_v4(_series("1d"), "NSW1")
    assert ds is not None
    return ds.model_dump_json(exclude_unset=True)


# name -> (rows_for, coroutine fn)
CASES: dict[str, tuple[Callable[[str], list[tuple]], Callable[[], Awaitable[str]]]] = {
    "power_week": (_power_rows, _power_week),
    "power_flows_per_interval": (_flow_rows, _flows),
    "energy_fueltech_daily": (_energy_rows, _energy),
    "demand_network_region_daily": (_demand_rows, _demand),
    "curtailment_network_region_daily": (_curtail_rows, _curtailment),
    "energy_interconnector_v4": (_flow_rows, _interconnector),
}


@pytest.mark.asyncio
@pytest.mark.parametrize("name", list(CASES))
async def test_export_output_byte_identical(
    name: str, install_client: Callable[..., FakeClient], monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pg(monkeypatch)
    rows_for, fn = CASES[name]
    install_client(rows_for)
    out = _norm(await fn())
    golden: dict[str, str] = json.loads(GOLDEN.read_text()) if GOLDEN.exists() else {}
    if os.environ.get("UPDATE_GOLDEN"):
        golden[name] = out
        GOLDEN.write_text(json.dumps(golden, indent=1, sort_keys=True))
        return
    assert out == golden[name]


@pytest.mark.asyncio
@pytest.mark.parametrize("name", list(CASES))
async def test_export_read_does_not_block_event_loop(
    name: str, install_client: Callable[..., FakeClient], monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pg(monkeypatch)
    rows_for, fn = CASES[name]
    # power_week does two CH reads (0.3s each), others one
    install_client(rows_for, delay=0.3)
    ticks = 0
    stop = asyncio.Event()

    async def ticker() -> None:
        nonlocal ticks
        while not stop.is_set():
            await asyncio.sleep(0.05)
            ticks += 1

    t = asyncio.create_task(ticker())
    await fn()
    stop.set()
    await t
    # one 0.3s read -> ~6 ticks; blocking code yields ~0
    assert ticks >= 5, f"loop starved: {ticks} ticks"


@pytest.mark.asyncio
async def test_concurrent_export_reads_do_not_share_a_connection(install_client: Callable[..., FakeClient]) -> None:
    fake = install_client(_flow_rows, delay=0.2)
    outs = await asyncio.gather(*(_flows() for _ in range(4)))
    assert len(set(outs)) == 1
    assert not fake.reentered
    # reads ran off the loop thread
    assert threading.get_ident() not in fake.threads
