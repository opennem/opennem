"""Tests for flow solver v4 — dynamic topology, polars-based."""

from datetime import datetime

import polars as pl
import pytest

from opennem.core.flow_solver_v4 import (
    compute_region_flows,
    solve_flow_emissions_consumption_mix,
    solve_flow_emissions_simple,
    solve_flows_v4,
)
from opennem.core.interconnector_topology import (
    NEM_DEFAULT_TOPOLOGY,
    NEM_PEC_TOPOLOGY,
)

TEST_INTERVAL = datetime.fromisoformat("2023-01-01T00:00:00")


# --- Fixtures from Simon's spreadsheet ---
# https://docs.google.com/spreadsheets/d/12eAnLYSdXJ55I06m0sRfrJyVd-1gGsSr/edit#gid=1210585319


def _region_emissions_df() -> pl.DataFrame:
    """Regional generation and emissions for test interval."""
    return pl.DataFrame(
        {
            "interval": [TEST_INTERVAL] * 5,
            "network_region": ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"],
            "energy": [500.0, 600.0, 300.0, 100.0, 80.0],
            "emissions": [325.0, 330.0, 180.0, 15.0, 4.0],
            "emissions_intensity": [0.65, 0.55, 0.60, 0.15, 0.05],
        }
    )


def _interconnector_df() -> pl.DataFrame:
    """Interconnector flows for test interval.

    VIC1->SA1: 22 MWh, NSW1->QLD1: -55 MWh (i.e. QLD1->NSW1 55),
    TAS1->VIC1: 11 MWh, VIC1->NSW1: 27.5 MWh
    """
    return pl.DataFrame(
        {
            "interval": [TEST_INTERVAL] * 4,
            "interconnector_region_from": ["VIC1", "NSW1", "TAS1", "VIC1"],
            "interconnector_region_to": ["SA1", "QLD1", "VIC1", "NSW1"],
            "energy": [22.0, -55.0, 11.0, 27.5],
        }
    )


# --- Tests ---


class TestNetworkTopology:
    def test_default_topology_regions(self):
        assert NEM_DEFAULT_TOPOLOGY.regions == ("NSW1", "QLD1", "SA1", "TAS1", "VIC1")

    def test_default_topology_flows(self):
        assert NEM_DEFAULT_TOPOLOGY.num_flows == 8

    def test_pec_topology_has_extra_flows(self):
        assert NEM_PEC_TOPOLOGY.num_flows == 10
        assert ("NSW1", "SA1") in NEM_PEC_TOPOLOGY.flows
        assert ("SA1", "NSW1") in NEM_PEC_TOPOLOGY.flows

    def test_flows_into(self):
        into_vic = NEM_DEFAULT_TOPOLOGY.flows_into("VIC1")
        assert ("NSW1", "VIC1") in into_vic
        assert ("SA1", "VIC1") in into_vic
        assert ("TAS1", "VIC1") in into_vic

    def test_flows_out_of(self):
        out_of_vic = NEM_DEFAULT_TOPOLOGY.flows_out_of("VIC1")
        assert ("VIC1", "NSW1") in out_of_vic
        assert ("VIC1", "SA1") in out_of_vic
        assert ("VIC1", "TAS1") in out_of_vic

    def test_region_index(self):
        idx = NEM_DEFAULT_TOPOLOGY.region_index
        assert len(idx) == 5
        assert idx["NSW1"] == 0


class TestComputeRegionFlows:
    def test_basic_flows(self):
        result = compute_region_flows(NEM_DEFAULT_TOPOLOGY, _interconnector_df())

        nsw = result.filter(pl.col("network_region") == "NSW1")
        assert nsw["energy_imports"][0] == pytest.approx(82.5, abs=0.1)
        assert nsw["energy_exports"][0] == pytest.approx(0.0, abs=0.1)

        qld = result.filter(pl.col("network_region") == "QLD1")
        assert qld["energy_exports"][0] == pytest.approx(55.0, abs=0.1)

        vic = result.filter(pl.col("network_region") == "VIC1")
        assert vic["energy_exports"][0] == pytest.approx(49.5, abs=0.1)
        assert vic["energy_imports"][0] == pytest.approx(11.0, abs=0.1)

    def test_empty_df(self):
        empty = pl.DataFrame(
            schema={
                "interval": pl.Datetime,
                "interconnector_region_from": pl.String,
                "interconnector_region_to": pl.String,
                "energy": pl.Float64,
            }
        )
        result = compute_region_flows(NEM_DEFAULT_TOPOLOGY, empty)
        assert result.is_empty()


class TestSimpleEmissions:
    """Simple method: flow emissions = flow energy * source region generation intensity."""

    def test_spreadsheet_energy(self):
        result = solve_flow_emissions_simple(NEM_DEFAULT_TOPOLOGY, _interconnector_df(), _region_emissions_df())

        nsw = result.filter(pl.col("network_region") == "NSW1")
        assert nsw["energy_imports"][0] == pytest.approx(82.5, abs=0.1)

        vic = result.filter(pl.col("network_region") == "VIC1")
        assert vic["energy_exports"][0] == pytest.approx(49.5, abs=0.1)
        assert vic["energy_imports"][0] == pytest.approx(11.0, abs=0.1)

    def test_simple_emissions_values(self):
        """Simple method: VIC1 exports at VIC1's generation intensity (0.60)."""
        result = solve_flow_emissions_simple(NEM_DEFAULT_TOPOLOGY, _interconnector_df(), _region_emissions_df())

        # TAS1 exports 11 at intensity 0.05 = 0.55
        tas = result.filter(pl.col("network_region") == "TAS1")
        assert tas["emissions_exports"][0] == pytest.approx(0.55, abs=0.01)

        # QLD1 exports 55 at intensity 0.65 = 35.75
        qld = result.filter(pl.col("network_region") == "QLD1")
        assert qld["emissions_exports"][0] == pytest.approx(35.75, abs=0.01)

        # VIC1 exports 49.5 at intensity 0.60 = 29.7 (simple method)
        vic = result.filter(pl.col("network_region") == "VIC1")
        assert vic["emissions_exports"][0] == pytest.approx(29.7, abs=0.1)

        # NSW1 imports: 55 * 0.65 + 27.5 * 0.60 = 35.75 + 16.5 = 52.25
        nsw = result.filter(pl.col("network_region") == "NSW1")
        assert nsw["emissions_imports"][0] == pytest.approx(52.25, abs=0.1)

    def test_all_values_non_negative(self):
        result = solve_flow_emissions_simple(NEM_DEFAULT_TOPOLOGY, _interconnector_df(), _region_emissions_df())
        for col in ["energy_imports", "energy_exports", "emissions_imports", "emissions_exports"]:
            assert (result[col] >= 0).all(), f"{col} has negative values"


class TestConsumptionMixEmissions:
    """Consumption-mix method: accounts for transit flows through intermediate regions.

    Expected values from Simon's spreadsheet which uses this methodology.
    """

    def test_spreadsheet_emissions(self):
        """VIC1 exports at consumption-mix intensity (~0.5806) not generation intensity (0.60)."""
        result = solve_flow_emissions_consumption_mix(NEM_DEFAULT_TOPOLOGY, _interconnector_df(), _region_emissions_df())

        # SA1 imports 22 from VIC1 at VIC1 consumption-mix intensity
        # VIC1 mix: (180 + 11*0.05) / (300 + 11) = 180.55/311 ≈ 0.5806
        # SA1 import emissions ≈ 22 * 0.5806 ≈ 12.77
        sa = result.filter(pl.col("network_region") == "SA1")
        assert sa["emissions_imports"][0] == pytest.approx(12.8, abs=0.2)

        # VIC1 exports ≈ 49.5 * 0.5806 ≈ 28.74
        vic = result.filter(pl.col("network_region") == "VIC1")
        assert vic["emissions_exports"][0] == pytest.approx(28.7, abs=0.2)

        # NSW1 imports: 55 * 0.65 + 27.5 * 0.5806 ≈ 35.75 + 15.97 ≈ 51.72
        nsw = result.filter(pl.col("network_region") == "NSW1")
        assert nsw["emissions_imports"][0] == pytest.approx(51.7, abs=0.2)

    def test_all_values_non_negative(self):
        result = solve_flow_emissions_consumption_mix(NEM_DEFAULT_TOPOLOGY, _interconnector_df(), _region_emissions_df())
        for col in ["energy_imports", "energy_exports", "emissions_imports", "emissions_exports"]:
            assert (result[col] >= 0).all(), f"{col} has negative values"


class TestPECTopology:
    """Test with Project EnergyConnect topology (NSW1<->SA1 loop)."""

    def _pec_interconnector_df(self) -> pl.DataFrame:
        """Add NSW1->SA1 flow to existing data."""
        return pl.DataFrame(
            {
                "interval": [TEST_INTERVAL] * 5,
                "interconnector_region_from": ["VIC1", "NSW1", "TAS1", "VIC1", "NSW1"],
                "interconnector_region_to": ["SA1", "QLD1", "VIC1", "NSW1", "SA1"],
                "energy": [22.0, -55.0, 11.0, 27.5, 15.0],  # NSW1->SA1: 15 MWh
            }
        )

    def test_simple_solves(self):
        """Simple method should work with loop topology."""
        result = solve_flow_emissions_simple(NEM_PEC_TOPOLOGY, self._pec_interconnector_df(), _region_emissions_df())
        assert not result.is_empty()
        assert len(result) == 5  # 5 regions

        # SA1 now imports from both VIC1 (22) and NSW1 (15) = 37
        sa = result.filter(pl.col("network_region") == "SA1")
        assert sa["energy_imports"][0] == pytest.approx(37.0, abs=0.1)

    def test_consumption_mix_solves(self):
        """Consumption-mix method should handle loop without error."""
        result = solve_flow_emissions_consumption_mix(NEM_PEC_TOPOLOGY, self._pec_interconnector_df(), _region_emissions_df())
        assert not result.is_empty()
        assert len(result) == 5

        # All values non-negative
        for col in ["energy_imports", "energy_exports", "emissions_imports", "emissions_exports"]:
            assert (result[col] >= 0).all(), f"{col} has negative values"


class TestSolveFlowsV4:
    def test_dispatch_simple(self):
        result = solve_flows_v4(
            NEM_DEFAULT_TOPOLOGY,
            _interconnector_df(),
            _region_emissions_df(),
            use_consumption_mix=False,
        )
        assert not result.is_empty()

    def test_dispatch_consumption_mix(self):
        result = solve_flows_v4(
            NEM_DEFAULT_TOPOLOGY,
            _interconnector_df(),
            _region_emissions_df(),
            use_consumption_mix=True,
        )
        assert not result.is_empty()

    def test_empty_interconnector_data(self):
        empty = pl.DataFrame(
            schema={
                "interval": pl.Datetime,
                "interconnector_region_from": pl.String,
                "interconnector_region_to": pl.String,
                "energy": pl.Float64,
            }
        )
        result = solve_flows_v4(NEM_DEFAULT_TOPOLOGY, empty, _region_emissions_df())
        assert result.is_empty()


class TestZeroEdgeCases:
    def test_zero_energy_region(self):
        """Region with zero generation should have zero emissions intensity."""
        regions = pl.DataFrame(
            {
                "interval": [TEST_INTERVAL] * 5,
                "network_region": ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"],
                "energy": [500.0, 600.0, 300.0, 0.0, 80.0],  # SA1 has zero
                "emissions": [325.0, 330.0, 180.0, 0.0, 4.0],
                "emissions_intensity": [0.65, 0.55, 0.60, 0.0, 0.05],
            }
        )
        result = solve_flow_emissions_simple(NEM_DEFAULT_TOPOLOGY, _interconnector_df(), regions)
        assert not result.is_empty()

    def test_all_zero_flows(self):
        """All interconnector flows are zero."""
        zero_flows = pl.DataFrame(
            {
                "interval": [TEST_INTERVAL] * 4,
                "interconnector_region_from": ["VIC1", "NSW1", "TAS1", "VIC1"],
                "interconnector_region_to": ["SA1", "QLD1", "VIC1", "NSW1"],
                "energy": [0.0, 0.0, 0.0, 0.0],
            }
        )
        result = solve_flow_emissions_simple(NEM_DEFAULT_TOPOLOGY, zero_flows, _region_emissions_df())
        # All flows should be zero
        for col in ["energy_imports", "energy_exports", "emissions_imports", "emissions_exports"]:
            assert (result[col] == 0).all(), f"{col} should be all zeros"
