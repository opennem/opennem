"""market_summary energy columns must come out in MWh, not GWh.

`_prepare_market_summary_data` turns MW demand/generation into per-interval energy by trapezoid
averaging and dividing by intervals_per_hour. That already yields MWh. A trailing `/ 1000` (commented
"Convert from kWh to MWh", but the inputs were never kW) left every energy column — and the market
values derived from them — 1000x low, so ClickHouse held GWh under an MWh label. That is #605: VIC1
July 2026 read 4,745 "MWh" for a month averaging 6,383 MW, i.e. 4.75 TWh.

The function is async and joins flow data from ClickHouse, so `_compute_flows_for_range` is patched
out; the energy arithmetic itself is pure and is what these tests pin.
"""

from datetime import datetime
from typing import Any

import pytest

from opennem.aggregates import market_summary as market_summary_mod

# Positional layout of the result tuples, per the final `result_df.select` in the module.
IDX_DEMAND_ENERGY = 8
IDX_DEMAND_TOTAL_ENERGY = 9
IDX_DEMAND_GROSS_ENERGY = 10
IDX_GENERATION_RENEWABLE_ENERGY = 11
IDX_DEMAND_MARKET_VALUE = 12
IDX_DEMAND_TOTAL_MARKET_VALUE = 13
IDX_CURTAILMENT_ENERGY_SOLAR = 18
IDX_CURTAILMENT_ENERGY_WIND = 19
IDX_RENEWABLE_WITH_STORAGE_ENERGY = 22


@pytest.fixture
def no_flows(monkeypatch):
    """Flows come from ClickHouse and are irrelevant here — null them out."""

    async def _no_flows(start_time, end_time):
        return None

    monkeypatch.setattr(market_summary_mod, "_compute_flows_for_range", _no_flows)


async def _prepare(records: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    """Run the aggregation. The declared return tuple is narrower than the 30 columns actually
    selected, so the rows are widened here rather than indexed against a stale annotation."""
    return list(await market_summary_mod._prepare_market_summary_data(records))  # type: ignore[arg-type]


def _record(network_id: str) -> tuple[Any, ...]:
    """One interval where every MW input is flat across the trapezoid, so energy = MW / intervals_per_hour."""
    return (
        datetime(2026, 7, 1, 0, 5),
        network_id,
        "VIC1",
        100.0,  # price
        6000.0,  # demand
        6600.0,  # demand_total
        6000.0,  # prev_demand
        6600.0,  # prev_demand_total
        400.0,  # rooftop_solar
        400.0,  # prev_rooftop_solar
        1200.0,  # renewable_generation
        1200.0,  # prev_renewable_generation
        60.0,  # storage_generation
        60.0,  # prev_storage_generation
        24.0,  # curtailment_solar_total
        120.0,  # curtailment_wind_total
        24.0,  # prev_curtailment_solar_total
        120.0,  # prev_curtailment_wind_total
        144.0,  # curtailment_total
    )


@pytest.mark.asyncio
async def test_nem_demand_energy_is_mwh_not_gwh(no_flows) -> None:
    (row,) = await _prepare([_record("NEM")])

    # 6000 MW held for one 5-minute interval = 6000 / 12 = 500 MWh. The GWh bug gave 0.5.
    assert row[IDX_DEMAND_ENERGY] == pytest.approx(500.0)
    assert row[IDX_DEMAND_TOTAL_ENERGY] == pytest.approx(550.0)


@pytest.mark.asyncio
async def test_wem_uses_30_minute_intervals(no_flows) -> None:
    (row,) = await _prepare([_record("WEM")])

    # WEM publishes 30-minute intervals, so intervals_per_hour is 2: 6000 / 2 = 3000 MWh.
    assert row[IDX_DEMAND_ENERGY] == pytest.approx(3000.0)
    assert row[IDX_DEMAND_TOTAL_ENERGY] == pytest.approx(3300.0)


@pytest.mark.asyncio
async def test_all_energy_columns_share_the_mwh_scale(no_flows) -> None:
    """demand_gross_energy must stay above demand_energy — the half-fix that leaves the siblings in
    GWh makes gross read 1000x below net on the same API response."""
    (row,) = await _prepare([_record("NEM")])

    # demand_gross = demand_total + rooftop = 7000 MW -> 583.3333 MWh
    assert row[IDX_DEMAND_GROSS_ENERGY] == pytest.approx(583.3333, abs=1e-4)
    assert row[IDX_DEMAND_GROSS_ENERGY] > row[IDX_DEMAND_ENERGY]

    # generation_renewable = renewable + rooftop = 1600 MW -> 133.3333 MWh
    assert row[IDX_GENERATION_RENEWABLE_ENERGY] == pytest.approx(133.3333, abs=1e-4)
    # + storage 60 MW = 1660 MW -> 138.3333 MWh
    assert row[IDX_RENEWABLE_WITH_STORAGE_ENERGY] == pytest.approx(138.3333, abs=1e-4)

    assert row[IDX_CURTAILMENT_ENERGY_SOLAR] == pytest.approx(2.0)
    assert row[IDX_CURTAILMENT_ENERGY_WIND] == pytest.approx(10.0)


@pytest.mark.asyncio
async def test_market_value_is_dollars_at_mwh_scale(no_flows) -> None:
    (row,) = await _prepare([_record("NEM")])

    # 500 MWh at $100/MWh = $50,000. The GWh bug made this $50 and the v3 export compensated with a
    # x1000 that has been removed alongside this fix.
    assert row[IDX_DEMAND_MARKET_VALUE] == pytest.approx(50_000.0)
    assert row[IDX_DEMAND_TOTAL_MARKET_VALUE] == pytest.approx(55_000.0)


@pytest.mark.asyncio
async def test_energy_matches_mw_average_over_the_hour(no_flows) -> None:
    """Twelve 5-minute NEM intervals at a flat 6000 MW must sum to 6000 MWh for the hour."""
    records = [_record("NEM") for _ in range(12)]
    rows = await _prepare(records)

    assert sum(row[IDX_DEMAND_ENERGY] or 0 for row in rows) == pytest.approx(6000.0)
