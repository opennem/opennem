"""Pollution endpoint: no per-pollutant substance lookups (N+1)."""

from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest

from opennem.api.pollution import router as pollution_router

pytestmark = pytest.mark.asyncio


class _Session:
    def __init__(self, facilities: list[Any], rows: list[Any], log: list[str]) -> None:
        self.facilities, self.rows, self.log = facilities, rows, log

    async def __aenter__(self) -> "_Session":
        return self

    async def __aexit__(self, *a: Any) -> None:
        return None

    async def execute(self, stmt: Any) -> Any:
        self.log.append(str(stmt))
        if len(self.log) == 1:
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: self.facilities))
        if len(self.log) == 2:
            return SimpleNamespace(all=lambda: self.rows)
        # per-pollutant substance lookup (old behaviour)
        code = next(r[1] for r in self.rows if r[1].code in str(stmt.compile().params.values()))
        return SimpleNamespace(scalar_one=lambda: code)


def _data() -> tuple[list[Any], list[Any]]:
    facs = [
        SimpleNamespace(code="F2", name="Second", npi_id="N2"),
        SimpleNamespace(code="F1", name="First", npi_id="N1"),
    ]
    subs = {
        c: SimpleNamespace(code=c, npi_name=f"name-{c}", category="air_pollutant", cas_number=None)
        for c in ("NOX", "SO2", "PM10")
    }
    rows = []
    for npi in ("N1", "N2"):
        for c in ("NOX", "SO2", "PM10"):
            for y in (2020, 2021):
                p = SimpleNamespace(
                    npi_facility_id=npi, substance_code=c, report_year=y, pollution_value=float(y), data_quality=None
                )
                rows.append((p, subs[c], None))
    return facs, rows


async def _run(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, list[str]]:
    log: list[str] = []
    facs, rows = _data()
    monkeypatch.setattr(pollution_router, "get_read_session", lambda: _Session(facs, rows, log))
    resp = await pollution_router.get_facility_pollution(
        user=None,  # pyright: ignore[reportArgumentType]
        facility_code=None,
        pollutant_code=None,
        pollutant_category=None,
        date_start=None,
        date_end=None,
    )
    return resp, log


async def test_pollution_query_count_constant(monkeypatch: pytest.MonkeyPatch) -> None:
    resp, log = await _run(monkeypatch)
    assert len(log) == 2  # facilities + pollution join; was 2 + one per pollutant
    assert [ts.results[0].columns["pollutant_code"] for ts in resp.data] == ["NOX", "SO2", "PM10"]
    first = resp.data[0]
    assert [r.name for r in first.results] == ["F1", "F2"]
    assert [r.columns["facility_name"] for r in first.results] == ["First", "Second"]
    assert first.results[0].data == [(datetime(2020, 7, 1), 2020.0), (datetime(2021, 7, 1), 2021.0)]
