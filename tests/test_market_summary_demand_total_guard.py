"""A collapsed DEMAND_AND_NONSCHEDGEN must not reach demand_gross (#661).

On 2024-05-22 11:45 AEMO published demand_total near zero in every NEM region while TOTALDEMAND
(demand) was normal, so demand_gross dropped to a third and the renewable proportion read 175%.
`_prepare_market_summary_data` now nulls demand_total when it is below half of demand and demand is
above 200 MW. SA1's genuinely near-zero midday operational demand must not trip it.
"""

from datetime import datetime
from typing import Any

import pytest

from opennem.aggregates import market_summary as market_summary_mod

# Positional layout of the result tuples, per the final `result_df.select` in the module.
IDX_DEMAND = 4
IDX_DEMAND_TOTAL = 5
IDX_DEMAND_GROSS = 6
IDX_GENERATION_RENEWABLE = 7
IDX_DEMAND_ENERGY = 8
IDX_DEMAND_TOTAL_ENERGY = 9
IDX_DEMAND_GROSS_ENERGY = 10
IDX_DEMAND_GROSS_MARKET_VALUE = 14


@pytest.fixture
def no_flows(monkeypatch):
    async def _no_flows(start_time, end_time):
        return None

    monkeypatch.setattr(market_summary_mod, "_compute_flows_for_range", _no_flows)


async def _prepare(records: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    return list(await market_summary_mod._prepare_market_summary_data(records))  # type: ignore[arg-type]


def _record(
    region: str,
    demand: float,
    demand_total: float,
    prev_demand: float,
    prev_demand_total: float,
    rooftop: float = 1000.0,
) -> tuple[Any, ...]:
    return (
        datetime(2024, 5, 22, 11, 45),
        "NEM",
        region,
        50.0,  # price
        demand,
        demand_total,
        prev_demand,
        prev_demand_total,
        rooftop,  # rooftop_solar
        rooftop,  # prev_rooftop_solar
        2000.0,  # renewable_generation
        2000.0,  # prev_renewable_generation
        0.0,  # storage_generation
        0.0,  # prev_storage_generation
        0.0,  # curtailment_solar_total
        0.0,  # curtailment_wind_total
        0.0,  # prev_curtailment_solar_total
        0.0,  # prev_curtailment_wind_total
        0.0,  # curtailment_total
    )


@pytest.mark.asyncio
async def test_collapsed_demand_total_is_nulled(no_flows) -> None:
    # NSW1 2024-05-22 11:45 from the MMSDM archive quoted in #661
    (row,) = await _prepare([_record("NSW1", 5977.81, 112.3158, 5990.0, 6400.0)])

    assert row[IDX_DEMAND_TOTAL] is None
    assert row[IDX_DEMAND_GROSS] is None
    assert row[IDX_DEMAND_TOTAL_ENERGY] is None
    assert row[IDX_DEMAND_GROSS_ENERGY] is None
    assert row[IDX_DEMAND_GROSS_MARKET_VALUE] is None

    # TOTALDEMAND and generation are fine and must survive
    assert row[IDX_DEMAND] == pytest.approx(5977.81)
    assert row[IDX_DEMAND_ENERGY] is not None
    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(3000.0)


@pytest.mark.asyncio
async def test_collapsed_prev_demand_total_does_not_leak_into_next_energy(no_flows) -> None:
    # the interval after the collapse: its own demand_total is fine, but the LAG carries the collapse
    (row,) = await _prepare([_record("NSW1", 6000.0, 6400.0, 5977.81, 112.3158)])

    assert row[IDX_DEMAND_TOTAL] == pytest.approx(6400.0)
    assert row[IDX_DEMAND_GROSS] == pytest.approx(7400.0)
    # the trapezoid has no valid left edge, so energy is NULL rather than half the real value
    assert row[IDX_DEMAND_GROSS_ENERGY] is None
    assert row[IDX_DEMAND_TOTAL_ENERGY] is None


@pytest.mark.asyncio
async def test_normal_row_kept(no_flows) -> None:
    (row,) = await _prepare([_record("VIC1", 4763.79, 5100.0, 4750.0, 5090.0)])

    assert row[IDX_DEMAND_TOTAL] == pytest.approx(5100.0)
    assert row[IDX_DEMAND_GROSS] == pytest.approx(6100.0)
    assert row[IDX_DEMAND_GROSS_ENERGY] == pytest.approx((6100.0 + 6090.0) / 2 / 12)


@pytest.mark.asyncio
async def test_sa1_near_zero_operational_demand_kept(no_flows) -> None:
    # SA1 midday: TOTALDEMAND itself is near zero, so a tiny demand_total is genuine
    (row,) = await _prepare([_record("SA1", 45.0, 3.0, 60.0, 0.0, rooftop=1800.0)])

    assert row[IDX_DEMAND_TOTAL] == pytest.approx(3.0)
    assert row[IDX_DEMAND_GROSS] == pytest.approx(1803.0)
    assert row[IDX_DEMAND_GROSS_ENERGY] == pytest.approx((1803.0 + 1800.0) / 2 / 12)


@pytest.mark.asyncio
async def test_threshold_is_strictly_below_half(no_flows) -> None:
    (row,) = await _prepare([_record("QLD1", 4000.0, 2000.0, 4000.0, 2000.0)])

    assert row[IDX_DEMAND_TOTAL] == pytest.approx(2000.0)
