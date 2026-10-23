"""Row-to-timeseries helpers run off the event loop (#730) and match the old inline path."""

import asyncio
import copy
import threading
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import patch

from opennem.api.queries import QueryType, get_timeseries_query
from opennem.api.timeseries import (
    build_timeseries_response,
    format_timeseries_response,
    rows_to_timeseries_list,
    rows_to_timeseries_response,
)
from opennem.api.utils import get_api_network_from_code
from opennem.core.grouping import PrimaryGrouping, SecondaryGrouping
from opennem.core.metric import Metric
from opennem.core.time_interval import Interval

_METRICS = [Metric.POWER, Metric.ENERGY]
_FUELTECHS = ["coal_black", "solar_utility", "wind", "gas_ccgt"]
_REGIONS = ["NSW1", "VIC1"]


def _setup() -> tuple[list[str], list[tuple[Any, ...]]]:
    network = get_api_network_from_code("NEM")
    start = datetime(2026, 1, 1)
    _, _, columns = get_timeseries_query(
        query_type=QueryType.DATA,
        network=network,
        metrics=_METRICS,
        interval=Interval.INTERVAL,
        date_start=start,
        date_end=start + timedelta(hours=4),
        primary_grouping=PrimaryGrouping.NETWORK_REGION,
        secondary_groupings=[SecondaryGrouping.FUELTECH],
    )
    rows: list[tuple[Any, ...]] = []
    for i in range(48):
        ts = start + timedelta(minutes=5 * i)
        for region in _REGIONS:
            for j, ft in enumerate(_FUELTECHS):
                values = {
                    "interval": ts,
                    "network_region": region,
                    "fueltech": ft,
                    "power": 100.0 + i + j,
                    "energy": None if i == 3 else 8.5 + j,
                }
                rows.append(tuple(values.get(c) for c in columns))
    return columns, rows


def _kwargs() -> dict[str, Any]:
    return {
        "network": "NEM",
        "metrics": _METRICS,
        "interval": Interval.INTERVAL,
        "primary_grouping": PrimaryGrouping.NETWORK_REGION,
        "secondary_groupings": [SecondaryGrouping.FUELTECH],
    }


def _inline(columns: list[str], rows: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    result_dicts = [dict(zip(columns, row, strict=True)) for row in rows]
    return format_timeseries_response(results=result_dicts, **_kwargs())


def test_helper_matches_inline_result() -> None:
    columns, rows = _setup()
    assert "interval" in columns

    expected = _inline(columns, copy.deepcopy(rows))
    assert expected and expected[0]["results"]

    assert rows_to_timeseries_list(columns, rows, **_kwargs()) == expected


def test_response_helper_matches_inline_payload() -> None:
    columns, rows = _setup()
    expected = build_timeseries_response(_inline(columns, rows))
    got = rows_to_timeseries_response(columns, rows, **_kwargs())

    assert got["data"] == expected["data"]
    assert set(got) == set(expected)
    assert got["version"] == expected["version"]


def test_helper_does_not_mutate_input_rows() -> None:
    columns, rows = _setup()
    snapshot = copy.deepcopy(rows)
    rows_to_timeseries_response(columns, rows, **_kwargs())
    assert rows == snapshot


async def _ticks_during(work: Any) -> tuple[int, Any]:
    ticks = 0
    stop = asyncio.Event()

    async def ticker() -> None:
        nonlocal ticks
        while not stop.is_set():
            await asyncio.sleep(0)
            ticks += 1

    task = asyncio.create_task(ticker())
    await asyncio.sleep(0)
    result = await work()
    stop.set()
    await task
    return ticks, result


def test_helper_runs_off_loop_thread() -> None:
    columns, rows = _setup()
    seen: list[int] = []
    real = format_timeseries_response

    def spy(**kw: Any) -> list[dict[str, Any]]:
        seen.append(threading.get_ident())
        return real(**kw)

    async def run() -> None:
        with patch("opennem.api.timeseries.format_timeseries_response", spy):
            await asyncio.to_thread(rows_to_timeseries_response, columns, rows, **_kwargs())

    main_ident = threading.get_ident()
    asyncio.run(run())
    assert seen
    assert main_ident not in seen


def test_loop_keeps_ticking_while_helper_runs() -> None:
    columns, rows = _setup()
    big = rows * 40  # enough work that a blocking call would starve the ticker

    async def run() -> int:
        ticks, _ = await _ticks_during(lambda: asyncio.to_thread(rows_to_timeseries_response, columns, big, **_kwargs()))
        return ticks

    assert asyncio.run(run()) > 5
