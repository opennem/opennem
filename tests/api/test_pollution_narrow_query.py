"""Pollution endpoint: narrow column select (no ORM entity hydration), response unchanged."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

from opennem.api.pollution import router as pollution_router

pytestmark = pytest.mark.asyncio

FIXTURE = Path(__file__).parent / "fixtures" / "pollution_expected.json"


class _Row:
    """Row usable by both shapes: flat attrs (narrow select) and (pollution, substance, facility) unpacking (old)."""

    def __init__(self, p: SimpleNamespace, s: SimpleNamespace) -> None:
        self._p, self._s = p, s
        self.npi_facility_id, self.report_year = p.npi_facility_id, p.report_year
        self.pollution_value, self.data_quality = p.pollution_value, p.data_quality
        self.code, self.npi_name, self.category, self.cas_number = s.code, s.npi_name, s.category, s.cas_number

    def __iter__(self) -> Any:
        return iter((self._p, self._s, None))


class _Session:
    def __init__(self, facilities: list[Any], rows: list[Any], log: list[Any]) -> None:
        self.facilities, self.rows, self.log = facilities, rows, log

    async def __aenter__(self) -> "_Session":
        return self

    async def __aexit__(self, *a: Any) -> None:
        return None

    async def execute(self, stmt: Any) -> Any:
        self.log.append(stmt)
        if len(self.log) == 1:
            rows = self.facilities
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows), all=lambda: rows)
        return SimpleNamespace(all=lambda: self.rows)


def _data(empty_rows: bool = False) -> tuple[list[Any], list[Any]]:
    facs = [
        SimpleNamespace(code="F2", name="Second", npi_id="N2"),
        SimpleNamespace(code="F1", name="First", npi_id="N1"),
        SimpleNamespace(code="F1", name="Dup", npi_id="N3"),  # same code, first name wins
    ]
    subs = {
        "NOX": SimpleNamespace(code="NOX", npi_name="Oxides of Nitrogen", category="air_pollutant", cas_number=None),
        "SO2": SimpleNamespace(code="SO2", npi_name="Sulfur dioxide", category="air_pollutant", cas_number="7446-09-5"),
        "PM10": SimpleNamespace(code="PM10", npi_name="PM10", category="air_pollutant", cas_number=None),
    }
    rows: list[Any] = []
    if empty_rows:
        return facs, rows
    for npi in ("N1", "N2", "N3", "UNKNOWN"):
        for c in ("NOX", "SO2", "PM10"):
            for i, y in enumerate((2019, 2020, 2022)):
                p = SimpleNamespace(
                    npi_facility_id=npi,
                    substance_code=c,
                    report_year=y,
                    pollution_value=Decimal("1234.5") * (i + 1) if i != 1 else Decimal("0"),
                    data_quality=None if i == 0 else ("measured" if i == 1 else "estimated"),
                )
                rows.append(_Row(p, subs[c]))
    return facs, rows


async def _run(monkeypatch: pytest.MonkeyPatch, facs: list[Any], rows: list[Any], **kw: Any) -> tuple[Any, list[Any]]:
    log: list[Any] = []
    monkeypatch.setattr(pollution_router, "get_read_session", lambda: _Session(facs, rows, log))
    args: dict[str, Any] = {
        "facility_code": None,
        "pollutant_code": None,
        "pollutant_category": None,
        "date_start": None,
        "date_end": None,
    }
    args.update(kw)
    resp = await pollution_router.get_facility_pollution(user=None, **args)  # pyright: ignore[reportArgumentType]
    return resp, log


async def test_response_equals_old_code_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    facs, rows = _data()
    resp, log = await _run(monkeypatch, facs, rows)
    assert len(log) == 2
    got = json.loads(resp.model_dump_json(exclude_none=True))
    got.pop("created_at", None)
    got.pop("version", None)
    if not FIXTURE.exists():  # generated once by the pre-change handler
        FIXTURE.write_text(json.dumps(got, indent=1, sort_keys=True))
    assert got == json.loads(FIXTURE.read_text())


async def test_ordering_and_grouping(monkeypatch: pytest.MonkeyPatch) -> None:
    facs, rows = _data()
    resp, _ = await _run(monkeypatch, facs, rows)
    assert [ts.results[0].columns["pollutant_code"] for ts in resp.data] == ["NOX", "SO2", "PM10"]
    assert [r.name for r in resp.data[0].results] == ["F1", "F2", "UNKNOWN"]
    assert resp.data[0].results[0].data[0] == (datetime(2019, 7, 1), 1234.5)


def _sql(stmt: Any) -> str:
    return str(stmt.compile())


async def test_pollution_statement_is_narrow(monkeypatch: pytest.MonkeyPatch) -> None:
    facs, rows = _data()
    _, log = await _run(monkeypatch, facs, rows)
    sel = _sql(log[1]).split("FROM")[0]
    for wide in ("pollution_unit", "pollution_subcategory", "pollution_category", "npi_pollution.id", "npi_facilities", "unit"):
        assert wide not in sel, wide
    for col in ("npi_facility_id", "report_year", "pollution_value", "data_quality", "npi_name", "cas_number", "category"):
        assert col in sel, col
    assert "ORDER BY npi_pollution.npi_facility_id, npi_pollution.substance_code, npi_pollution.report_year" in _sql(log[1])


async def test_facilities_statement_is_narrow(monkeypatch: pytest.MonkeyPatch) -> None:
    facs, rows = _data()
    _, log = await _run(monkeypatch, facs, rows)
    sel = _sql(log[0]).split("FROM")[0]
    assert "facilities.code" in sel and "facilities.name" in sel and "facilities.npi_id" in sel
    assert sel.count(",") <= 3


async def test_no_facilities_404(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(HTTPException) as e:
        await _run(monkeypatch, [], [], facility_code=["NOPE"])
    assert e.value.status_code == 404
    assert "NOPE" in e.value.detail


async def test_no_pollution_rows_404(monkeypatch: pytest.MonkeyPatch) -> None:
    facs, rows = _data(empty_rows=True)
    with pytest.raises(HTTPException) as e:
        await _run(monkeypatch, facs, rows)
    assert e.value.status_code == 404
    assert e.value.detail.startswith("No pollution data available")
