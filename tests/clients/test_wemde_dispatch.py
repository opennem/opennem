"""Unit tests for wemde_parse_dispatch — 5-min dispatch price extraction."""

from datetime import datetime

import pytest

from opennem.clients import wemde
from opennem.persistence.schema import BalancingSummarySchema, FacilityScadaSchema


def _make_dispatch_json(
    primary_interval: str = "2026-05-25T16:45:00+08:00",
    extra_interval: str = "2026-05-25T16:50:00+08:00",
    energy_price: float | None = 115.28,
) -> dict:
    """Build a minimal dispatch solution JSON with a binding interval and one look-ahead."""

    def _interval(ts: str, price: float | None) -> dict:
        prices: dict[str, float] = {}
        if price is not None:
            prices["energy"] = price
        return {
            "dispatchInterval": ts,
            "dispatchType": "Dispatch",
            "scenario": "Reference",
            "prices": prices,
            "schedule": [
                {
                    "marketService": "energy",
                    "facilitySchedule": [
                        {"facilityCode": "MUJA_G5", "quantity": 220.0},
                        {"facilityCode": "MUJA_G6", "quantity": 215.0},
                    ],
                }
            ],
        }

    return {
        "primaryDispatchInterval": primary_interval,
        "solutionData": [
            _interval(primary_interval, energy_price),
            # look-ahead interval — must be skipped by parser
            _interval(extra_interval, 999.0),
        ],
    }


@pytest.fixture()
def _patched_parser(monkeypatch):
    """Patch the network downloader + battery map so wemde_parse_dispatch is pure-fn."""

    async def _fake_dl(_url: str) -> list[dict]:
        return [_make_dispatch_json()]

    async def _fake_battery_map():
        return {}

    monkeypatch.setattr(wemde, "_wemde_download_dataset", _fake_dl)
    monkeypatch.setattr(wemde, "get_battery_unit_map", _fake_battery_map)


@pytest.mark.asyncio
async def test_wemde_dispatch_emits_facility_and_price(_patched_parser):
    """Binding interval yields facility_scada rows AND a balancing_summary price_dispatch row."""
    records = await wemde.wemde_parse_dispatch("ignored")

    fs = [r for r in records if isinstance(r, FacilityScadaSchema)]
    bs = [r for r in records if isinstance(r, BalancingSummarySchema)]

    # Two facility schedule entries → two FS rows; one binding interval → one BS row.
    # Look-ahead intervals must be skipped (no extra FS or BS rows).
    assert len(fs) == 2
    assert len(bs) == 1

    bs_row = bs[0]
    assert bs_row.network_id == "WEM"
    assert bs_row.network_region == "WEM"
    assert bs_row.price_dispatch == pytest.approx(115.28)
    # interval is tz-stripped binding interval
    assert bs_row.interval == datetime(2026, 5, 25, 16, 45)
    # FS rows all carry the binding interval, never the look-ahead
    assert all(r.interval == datetime(2026, 5, 25, 16, 45) for r in fs)


@pytest.mark.asyncio
async def test_wemde_dispatch_no_price_field(monkeypatch):
    """Missing prices.energy → FS rows still emitted, no BS row."""

    async def _fake_dl(_url: str) -> list[dict]:
        return [_make_dispatch_json(energy_price=None)]

    async def _fake_battery_map():
        return {}

    monkeypatch.setattr(wemde, "_wemde_download_dataset", _fake_dl)
    monkeypatch.setattr(wemde, "get_battery_unit_map", _fake_battery_map)

    records = await wemde.wemde_parse_dispatch("ignored")

    assert any(isinstance(r, FacilityScadaSchema) for r in records)
    assert not any(isinstance(r, BalancingSummarySchema) for r in records)
