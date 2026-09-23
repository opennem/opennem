"""A collapsed DEMAND_AND_NONSCHEDGEN or a missing input must not reach demand_gross (#661).

On 2024-05-22 11:45 AEMO published demand_total near zero in every NEM region while TOTALDEMAND
(demand) was normal, so demand_gross dropped to a third and the renewable proportion read 175%.
`_prepare_market_summary_data` now nulls demand_total when it is below half of demand and demand is
above 200 MW. SA1's genuinely near-zero midday operational demand must not trip it.

Renewable proportion is only valid when every input is present, so a NULL demand_total or a NULL
rooftop (once rooftop is an expected input) makes the gross/renewable family NULL instead of
silently computing it with 0. demand and price are never touched.
"""

import inspect
from datetime import datetime
from typing import Any

import pytest

from opennem.aggregates import market_summary as market_summary_mod

IDX_PRICE = 3

# Positional layout of the result tuples, per the final `result_df.select` in the module.
IDX_DEMAND = 4
IDX_DEMAND_TOTAL = 5
IDX_DEMAND_GROSS = 6
IDX_GENERATION_RENEWABLE = 7
IDX_DEMAND_ENERGY = 8
IDX_DEMAND_TOTAL_ENERGY = 9
IDX_DEMAND_GROSS_ENERGY = 10
IDX_GENERATION_RENEWABLE_ENERGY = 11
IDX_DEMAND_MARKET_VALUE = 12
IDX_DEMAND_GROSS_MARKET_VALUE = 14
IDX_GENERATION_RENEWABLE_WITH_STORAGE = 21
IDX_GENERATION_RENEWABLE_WITH_STORAGE_ENERGY = 22


@pytest.fixture
def no_flows(monkeypatch):
    async def _no_flows(start_time, end_time):
        return None

    monkeypatch.setattr(market_summary_mod, "_compute_flows_for_range", _no_flows)


async def _prepare(records: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
    return list(await market_summary_mod._prepare_market_summary_data(records))  # type: ignore[arg-type]


def _record(
    region: str,
    demand: float | None,
    demand_total: float | None,
    prev_demand: float | None,
    prev_demand_total: float | None,
    rooftop: float | None = 1000.0,
    prev_rooftop: float | None | str = "same",
    interval: datetime = datetime(2024, 5, 22, 11, 45),
    network_id: str = "NEM",
    scada_rows: int | None = 120,
    prev_scada_rows: int | None = 120,
    renewable: float | None = 2000.0,
) -> tuple[Any, ...]:
    return (
        interval,
        network_id,
        region,
        50.0,  # price
        demand,
        demand_total,
        prev_demand,
        prev_demand_total,
        rooftop,  # rooftop_solar
        rooftop if prev_rooftop == "same" else prev_rooftop,  # prev_rooftop_solar
        renewable,  # renewable_generation
        renewable,  # prev_renewable_generation
        0.0,  # storage_generation
        0.0,  # prev_storage_generation
        0.0,  # curtailment_solar_total
        0.0,  # curtailment_wind_total
        0.0,  # prev_curtailment_solar_total
        0.0,  # prev_curtailment_wind_total
        0.0,  # curtailment_total
        scada_rows,
        prev_scada_rows,
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
async def test_threshold_is_strictly_below_ratio(no_flows) -> None:
    (row,) = await _prepare([_record("QLD1", 4000.0, 3600.0, 4000.0, 3600.0)])

    assert row[IDX_DEMAND_TOTAL] == pytest.approx(3600.0)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("region", "demand", "demand_total"),
    [
        ("TAS1", 1119.19, 581.49953),  # 2018-01-22 11:15, read 192% renewable
        ("TAS1", 1118.76, 821.70524),  # 2023-03-14 14:55
        ("SA1", 259.51, 228.47488),  # 2016-09-28 19:40
    ],
)
async def test_partial_collapses_are_nulled(no_flows, region: str, demand: float, demand_total: float) -> None:
    (row,) = await _prepare([_record(region, demand, demand_total, demand, demand / 0.99)])

    assert row[IDX_DEMAND_TOTAL] is None
    assert row[IDX_DEMAND_GROSS] is None


def _assert_gross_family_null(row: tuple[Any, ...]) -> None:
    for idx in (
        IDX_DEMAND_GROSS,
        IDX_GENERATION_RENEWABLE,
        IDX_GENERATION_RENEWABLE_ENERGY,
        IDX_DEMAND_GROSS_ENERGY,
        IDX_DEMAND_GROSS_MARKET_VALUE,
        IDX_GENERATION_RENEWABLE_WITH_STORAGE,
        IDX_GENERATION_RENEWABLE_WITH_STORAGE_ENERGY,
    ):
        assert row[idx] is None, idx


@pytest.mark.asyncio
async def test_missing_rooftop_midday_nulls_gross_and_renewable(no_flows) -> None:
    # rooftop still NULL after the CTE's interpolation and bounded locf: unknown, not 0
    (row,) = await _prepare([_record("SA1", 900.0, 950.0, 900.0, 950.0, rooftop=None)])

    _assert_gross_family_null(row)
    assert row[IDX_DEMAND_TOTAL] == pytest.approx(950.0)
    assert row[IDX_DEMAND] == pytest.approx(900.0)
    assert row[IDX_DEMAND_ENERGY] == pytest.approx(75.0)
    assert row[IDX_DEMAND_MARKET_VALUE] == pytest.approx(75.0 * 50.0)
    assert row[IDX_PRICE] == pytest.approx(50.0)


@pytest.mark.asyncio
async def test_interpolated_rooftop_present(no_flows) -> None:
    # the CTE interpolated across a blank measurement (#660), so the value is there
    (row,) = await _prepare([_record("SA1", 900.0, 950.0, 900.0, 950.0, rooftop=1600.0, prev_rooftop=1550.0)])

    assert row[IDX_DEMAND_GROSS] == pytest.approx(2550.0)
    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(3600.0)
    assert row[IDX_DEMAND_GROSS_ENERGY] == pytest.approx((2550.0 + 2500.0) / 2 / 12)


@pytest.mark.asyncio
async def test_pre_rooftop_era_unchanged(no_flows) -> None:
    # before ROOFTOP_EXPECTED_FROM there is no rooftop term: a NULL is 0 as before
    (row,) = await _prepare([_record("NSW1", 7000.0, 7100.0, 7000.0, 7100.0, rooftop=None, interval=datetime(2012, 1, 5, 13, 0))])

    assert row[IDX_DEMAND_GROSS] == pytest.approx(7100.0)
    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(2000.0)
    assert row[IDX_DEMAND_GROSS_ENERGY] == pytest.approx(7100.0 / 12)


@pytest.mark.asyncio
async def test_rooftop_expected_boundary_uses_prev_bucket_era(no_flows) -> None:
    # first expected bucket: prev bucket is pre-cutoff, so its NULL rooftop is 0 and energy is kept
    boundary = market_summary_mod.ROOFTOP_EXPECTED_FROM
    (row,) = await _prepare([_record("NSW1", 7000.0, 7100.0, 7000.0, 7100.0, rooftop=10.0, prev_rooftop=None, interval=boundary)])

    assert row[IDX_DEMAND_GROSS] == pytest.approx(7110.0)
    assert row[IDX_DEMAND_GROSS_ENERGY] == pytest.approx((7110.0 + 7100.0) / 2 / 12)


@pytest.mark.asyncio
async def test_wem_rooftop_not_expected(no_flows) -> None:
    # WEM rooftop is not joined into market_summary, so it keeps the no-rooftop-term behaviour
    (row,) = await _prepare([_record("WEM", 2500.0, 2500.0, 2500.0, 2500.0, rooftop=None, network_id="WEM")])

    assert row[IDX_DEMAND_GROSS] == pytest.approx(2500.0)
    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(2000.0)


@pytest.mark.asyncio
async def test_missing_balancing_row_nulls_gross(no_flows) -> None:
    # no balancing_summary row for a NEM region/interval: demand and demand_total are NULL
    (row,) = await _prepare([_record("VIC1", None, None, 4750.0, 5090.0)])

    assert row[IDX_DEMAND_TOTAL] is None
    assert row[IDX_DEMAND_GROSS] is None
    assert row[IDX_DEMAND_GROSS_ENERGY] is None
    assert row[IDX_DEMAND_TOTAL_ENERGY] is None
    # renewable generation does not depend on demand
    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(3000.0)


@pytest.mark.asyncio
async def test_energy_null_when_prev_rooftop_null(no_flows) -> None:
    # current bucket is complete but the LAG rooftop is missing: no valid trapezoid
    (row,) = await _prepare([_record("QLD1", 6000.0, 6300.0, 6000.0, 6300.0, rooftop=3000.0, prev_rooftop=None)])

    assert row[IDX_DEMAND_GROSS] == pytest.approx(9300.0)
    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(5000.0)
    assert row[IDX_DEMAND_GROSS_ENERGY] is None
    assert row[IDX_GENERATION_RENEWABLE_ENERGY] is None
    assert row[IDX_GENERATION_RENEWABLE_WITH_STORAGE_ENERGY] is None
    # demand energy has its own complete inputs
    assert row[IDX_DEMAND_ENERGY] == pytest.approx(500.0)


def test_query_does_not_zero_fill_rooftop() -> None:
    # the SQL must hand a missing rooftop through as NULL; only the polars step may decide it is 0
    source = " ".join(inspect.getsource(market_summary_mod._get_market_summary_data).split())

    assert "COALESCE(rd.rooftop_solar, 0)" not in source
    assert "rd.rooftop_solar," in source


@pytest.mark.asyncio
async def test_region_with_no_scada_rows_nulls_renewable(no_flows) -> None:
    # ingest gap: no unit reported for the bucket, the CTE's interpolated value is not trusted
    (row,) = await _prepare([_record("QLD1", 6000.0, 6300.0, 6000.0, 6300.0, rooftop=3000.0, scada_rows=None)])

    assert row[IDX_GENERATION_RENEWABLE] is None
    assert row[IDX_GENERATION_RENEWABLE_WITH_STORAGE] is None
    assert row[IDX_GENERATION_RENEWABLE_ENERGY] is None
    assert row[IDX_GENERATION_RENEWABLE_WITH_STORAGE_ENERGY] is None
    # demand side has all its inputs
    assert row[IDX_DEMAND_GROSS] == pytest.approx(9300.0)
    assert row[IDX_DEMAND] == pytest.approx(6000.0)


@pytest.mark.asyncio
async def test_region_with_no_prev_scada_rows_nulls_renewable_energy(no_flows) -> None:
    (row,) = await _prepare([_record("QLD1", 6000.0, 6300.0, 6000.0, 6300.0, prev_scada_rows=0)])

    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(3000.0)
    assert row[IDX_GENERATION_RENEWABLE_ENERGY] is None


@pytest.mark.asyncio
async def test_units_reporting_zero_renewable_stays_zero(no_flows) -> None:
    # units reported, renewable output genuinely 0 (and the CTE may hand back NULL for it)
    (row,) = await _prepare(
        [_record("TAS1", 1000.0, 1050.0, 1000.0, 1050.0, rooftop=0.0, renewable=None, scada_rows=8, prev_scada_rows=8)]
    )

    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(0.0)
    assert row[IDX_GENERATION_RENEWABLE_ENERGY] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_scada_absence_before_era_keeps_zero_fill(no_flows) -> None:
    (row,) = await _prepare(
        [
            _record(
                "NSW1",
                7000.0,
                7100.0,
                7000.0,
                7100.0,
                rooftop=None,
                renewable=None,
                scada_rows=None,
                prev_scada_rows=None,
                interval=datetime(2012, 1, 5, 13, 0),
            )
        ]
    )

    assert row[IDX_GENERATION_RENEWABLE] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_wem_scada_absence_only_after_wemde_cutover(no_flows) -> None:
    # WEM facility_scada was 30-min before WEMDE, so empty 5-min buckets are normal there
    kw = {"rooftop": None, "network_id": "WEM", "scada_rows": None, "prev_scada_rows": None}
    (pre,) = await _prepare([_record("WEM", 2500.0, 2500.0, 2500.0, 2500.0, interval=datetime(2022, 6, 1, 12, 5), **kw)])
    (post,) = await _prepare([_record("WEM", 2500.0, 2500.0, 2500.0, 2500.0, interval=datetime(2025, 6, 1, 12, 5), **kw)])

    assert pre[IDX_GENERATION_RENEWABLE] == pytest.approx(2000.0)
    assert post[IDX_GENERATION_RENEWABLE] is None
    assert post[IDX_DEMAND_GROSS] == pytest.approx(2500.0)


def test_query_carries_scada_presence() -> None:
    source = " ".join(inspect.getsource(market_summary_mod._get_market_summary_data).split())

    assert "count(*) as scada_rows" in source
    assert "LAG(scada_rows) OVER" in source
    assert source.rstrip().count("prev_scada_rows") >= 2
