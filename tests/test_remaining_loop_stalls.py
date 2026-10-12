"""Event loop blockers left after #709/#712: bom backoff, wemde zip parse, forecast parse, CH schema ping, unit interval frame."""

import asyncio
import io
import json
import time
import zipfile
from collections.abc import Awaitable, Callable
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pandas as pd
import polars as pl
import pytest

from opennem.aggregates import forecast, market_summary, unit_intervals
from opennem.crawlers import bom
from opennem.utils import archive

TICK = 0.05


async def _max_gap(work: Callable[[], Awaitable[object]]) -> float:
    """Largest gap between 50ms ticker wake-ups while `work` runs; a blocked loop shows as a big gap"""
    gaps: list[float] = []
    stop = asyncio.Event()

    async def ticker() -> None:
        last = time.perf_counter()
        while not stop.is_set():
            await asyncio.sleep(TICK)
            now = time.perf_counter()
            gaps.append(now - last)
            last = now

    task = asyncio.create_task(ticker())
    await asyncio.sleep(0)
    try:
        await work()
    finally:
        stop.set()
        await task
    return max(gaps, default=0.0)


def _block(seconds: float) -> None:
    time.sleep(seconds)


@pytest.mark.asyncio
async def test_bom_backoff_does_not_block_loop() -> None:
    stations = [SimpleNamespace(code="X", name="X", feed_url="http://x")]
    crawler = SimpleNamespace(backoff=0.3, limit=None)

    with (
        patch.object(bom, "get_stations_priority", AsyncMock(return_value=stations)),
        patch.object(bom, "get_bom_observations", AsyncMock(return_value=[])),
        patch.object(bom, "store_bom_observation_intervals", AsyncMock(return_value=SimpleNamespace(last_modified=None))),
    ):
        gap = await _max_gap(lambda: bom.crawl_bom_capitals(crawler))  # type: ignore[arg-type]

    assert gap < 0.2


def _zip_bytes(docs: dict[str, object]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, doc in docs.items():
            zf.writestr(name, json.dumps(doc))
    return buf.getvalue()


class _FakeHttp:
    def __init__(self, content: bytes, content_type: str) -> None:
        self._response = SimpleNamespace(
            is_success=True, status_code=200, headers={"content-type": content_type}, content=content
        )

    async def get(self, url: str) -> SimpleNamespace:
        return self._response


@pytest.mark.asyncio
async def test_zip_parse_identical_and_cleans_temp_dir() -> None:
    docs = {"a.json": {"x": [1, 2]}, "b.json": [3]}
    seen: list[object] = []
    real_rmtree = archive.shutil.rmtree

    def spy(path: object) -> None:
        seen.append(path)
        real_rmtree(path)  # type: ignore[arg-type]

    with (
        patch.object(archive, "http_factory", lambda **_: _FakeHttp(_zip_bytes(docs), "application/zip")),
        patch.object(archive.shutil, "rmtree", spy),
    ):
        result = await archive.download_and_parse_json_zip("http://x/y.zip")

    assert result == [docs["a.json"], docs["b.json"]]
    assert len(seen) == 1 and not archive.Path(str(seen[0])).exists()


@pytest.mark.asyncio
async def test_plain_json_and_bad_json() -> None:
    with patch.object(archive, "http_factory", lambda **_: _FakeHttp(b'{"a": 1}', "application/json")):
        assert await archive.download_and_parse_json_zip("http://x") == [{"a": 1}]

    with patch.object(archive, "http_factory", lambda **_: _FakeHttp(b"{nope", "application/json")):
        with pytest.raises(Exception, match="Failed to parse JSON"):
            await archive.download_and_parse_json_zip("http://x")


@pytest.mark.asyncio
async def test_zip_parse_does_not_block_loop() -> None:
    real_loads = archive.json.load

    def slow_load(fp: object) -> object:
        time.sleep(0.4)
        return real_loads(fp)  # type: ignore[arg-type]

    with (
        patch.object(archive, "http_factory", lambda **_: _FakeHttp(_zip_bytes({"a.json": {}}), "application/zip")),
        patch.object(archive.json, "load", slow_load),
    ):
        gap = await _max_gap(lambda: archive.download_and_parse_json_zip("http://x/y.zip"))

    assert gap < 0.25


def test_forecast_naive_matches_direct_pandas_incl_odd_values() -> None:
    forecast._parse_naive_str.cache_clear()
    values = [
        "2026/10/06 11:30:00",
        "2026-10-06 11:30:00",
        "2026-10-06T11:30:00+10:00",
        "2026-10-06T01:30:00Z",
        "06/10/2026 11:30",
        datetime(2026, 10, 6, 11, 30),
        pd.Timestamp("2026-10-06 11:30"),
    ]
    for value in values * 2:
        assert forecast._naive(value) == pd.to_datetime(value).to_pydatetime().replace(tzinfo=None)

    for bad in ("", "not a date", "2026/13/45 99:99:99"):
        try:
            expected: object = pd.to_datetime(bad).to_pydatetime()
        except Exception as e:
            expected = type(e)
        if isinstance(expected, type):
            with pytest.raises(expected):
                forecast._naive(bad)
        else:
            got = forecast._naive(bad)
            want = expected.replace(tzinfo=None)  # type: ignore[attr-defined]
            assert (pd.isna(got) and pd.isna(want)) or got == want


def test_forecast_parses_each_distinct_string_once() -> None:
    forecast._parse_naive_str.cache_clear()
    records = [
        {
            "regionid": "NSW1",
            "powermean": "1",
            "interval_datetime": f"2026/10/06 {11 + i % 2}:00:00",
            "version_datetime": "2026/10/06 10:00:00",
        }
        for i in range(50)
    ]
    with patch.object(forecast, "_parse_naive", wraps=forecast._parse_naive) as spy:
        rows = forecast.rooftop_forecast_rows(records)

    assert len(rows) == 50
    assert spy.call_count == 3


@pytest.mark.asyncio
async def test_market_summary_schema_ensure_is_off_loop() -> None:
    threads: list[bool] = []
    main = asyncio.get_running_loop()

    def slow_ensure() -> None:
        threads.append(_in_loop_thread(main))
        time.sleep(0.4)

    with (
        patch.object(market_summary, "_ensure_clickhouse_schema", slow_ensure),
        patch.object(market_summary, "get_clickhouse_client", lambda: object()),
    ):
        gap = await _max_gap(
            lambda: market_summary.process_market_summary_backlog(
                None,  # type: ignore[arg-type]
                datetime(2026, 1, 2),
                datetime(2026, 1, 1),
            )
        )

    assert threads == [False]
    assert gap < 0.25


def _in_loop_thread(loop: asyncio.AbstractEventLoop) -> bool:
    try:
        return asyncio.get_running_loop() is loop
    except RuntimeError:
        return False


def _old_prepare(records: list[tuple]) -> list[tuple]:
    """Row-wise construction as it was before the column build"""
    df = pl.DataFrame(records, schema=unit_intervals._UNIT_INTERVAL_SCHEMA, orient="row")
    return df.rows()


def _record(i: int, region: str = "NSW1", renewable: bool | None = True, energy: float | None = 1.23456789) -> tuple:
    return (
        datetime(2026, 10, 6, 0, 5 * i),
        "NEM",
        region,
        f"FAC{i}",
        f"UNIT{i}",
        "operating",
        "solar_utility",
        "solar",
        renewable,
        10.123456 + i,
        energy,
        None,
        0.0,
        None,
        99.99999 + i,
    )


def test_prepare_unit_interval_data_dtypes_order_values() -> None:
    records = [_record(0), _record(1, "SNOWY1", False), _record(2, energy=None), _record(3, renewable=None)]

    prepared = unit_intervals._prepare_unit_interval_data(records)

    assert len(prepared) == 4 and all(len(r) == 16 for r in prepared)
    assert [r[2] for r in prepared] == ["NSW1", "NSW1", "NSW1", "NSW1"]  # SNOWY1 folded into NSW1
    assert [r[0] for r in prepared] == [r[0] for r in records]
    assert prepared[0][10] == 1.2346 and prepared[2][10] is None and prepared[3][8] is None
    assert unit_intervals._prepare_unit_interval_data([]) == []
    # same frame as a row-wise build, before the post-processing
    cols = pl.DataFrame(
        dict(zip(unit_intervals._UNIT_INTERVAL_SCHEMA, zip(*records, strict=True), strict=True)),
        schema=unit_intervals._UNIT_INTERVAL_SCHEMA,
    )
    assert cols.equals(pl.DataFrame(records, schema=unit_intervals._UNIT_INTERVAL_SCHEMA, orient="row"))
    assert cols.schema == pl.DataFrame(records, schema=unit_intervals._UNIT_INTERVAL_SCHEMA, orient="row").schema


@pytest.mark.asyncio
async def test_persist_facility_scada_bulk_converts_off_loop_and_unchanged() -> None:
    from opennem.persistence import postgres_facility_scada as pfs
    from opennem.persistence.schema import FacilityScadaSchema

    records = [
        FacilityScadaSchema(interval=datetime(2026, 1, 1, 0, i % 60), network_id="WEM", facility_code=f"F{i}", generated=i)
        for i in range(300_000)
    ]
    seen: list[list[dict]] = []

    async def fake_bulk(table: object, records: list[dict], update_fields: list[str]) -> int:
        seen.append(records)
        return len(records)

    with patch.object(pfs, "bulkinsert_mms_items", fake_bulk):
        gap = await _max_gap(lambda: pfs.persist_facility_scada_bulk(records, ["generated"]))

    assert seen[0] == [dict(r) for r in records]
    assert gap < 0.25


def test_bulk_insert_convert_records_coerces_types() -> None:
    from opennem.db.bulk_insert_csv import _convert_records

    rows = _convert_records(
        [{"a": "2026-01-01T00:05:00", "b": "1.5", "c": "t", "d": "7", "e": 3, "f": None}],
        ["a", "b", "c", "d", "e", "f"],
        {
            "a": "timestamp without time zone",
            "b": "numeric",
            "c": "boolean",
            "d": "integer",
            "e": "text",
            "f": "text",
        },
    )

    assert rows == [[datetime(2026, 1, 1, 0, 5), 1.5, True, 7, "3", None]]
