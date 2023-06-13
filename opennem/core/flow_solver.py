"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

This feature is enabled behind a feature flag in settings_schema.network_flows_v3

Unit tests are at tests/core/flow_solver.py

Documentation at: https://github.com/opennem/opennem/wiki/Network-Flows

"""

import logging
from dataclasses import dataclass
from typing import NewType

import numpy as np

from opennem.schema.network import NetworkSchema

# from result import Err, Ok, Result

logger = logging.getLogger("opennem.core.flow_solver")


class FlowSolverException(Exception):
    "Raised on issue with flow solver"
    pass


# ex. NSW1
Region = NewType("Region", str)

# ex. NSW1->QLD1
RegionFlow = NewType("RegionFlow", str)


# Region demand and emissions structures


@dataclass
class RegionDemandEmissions:
    """Emissions for each region

    Emissions are the sum of the emissions for that region plus the emissions
    of the imports minus the emissions of the exports
    """

    region_code: Region
    generated_mwh: float
    emissions_t: float


class NetworkRegionsDemandEmissions:
    """For a network contains a list of regions and the demand and emissions for each
    region.
    """

    def __init__(self, network: NetworkSchema, data: list[RegionDemandEmissions]):
        self.data = data
        self.network = network

    def __repr__(self) -> str:
        return f"<RegionNetEmissionsDemandForNetwork region_code={self.network.code} regions={len(self.data)}>"

    def get_region(self, region_code: Region) -> RegionDemandEmissions:
        """Get region by code"""
        region_result = next(filter(lambda x: x.region_code == region_code, self.data))

        if not region_result:
            raise FlowSolverException(f"Region {region_code} not found in network {self.network.code}")

        return region_result


# Interconnector flow generation and emissions structures
@dataclass
class InterconnectorNetEmissionsEnergy:
    """Power for each interconnector

    Power is the sum of the generation of the source region minus the exports
    """

    region_flow: RegionFlow
    generated_mwh: float
    emissions_t: float


class NetworkInterconnectorEnergyEmissions:
    """For a network contains a list of interconnectors and the emissions and generation for each"""

    def __init__(self, network: NetworkSchema, data: list[InterconnectorNetEmissionsEnergy]):
        self.data = data
        self.network = network

    def get_interconnector(self, region_flow: RegionFlow, default: int = 0) -> InterconnectorNetEmissionsEnergy:
        """Get interconnector by region flow"""
        interconnector_result = next(filter(lambda x: x.region_flow == region_flow, self.data))

        if not interconnector_result:
            if default:
                return InterconnectorNetEmissionsEnergy(region_flow=region_flow, generated_mwh=default, emissions_t=default)

            raise FlowSolverException(f"Interconnector {region_flow} not found in network {self.network.code}")

        return interconnector_result


# Flow solver return class
@dataclass
class FlowSolverResult:
    """ """

    region_flow: RegionFlow
    emissions: float


def solve_flow_emissions_for_interval(
    interconnector_data: NetworkInterconnectorEnergyEmissions,
    region_data: NetworkRegionsDemandEmissions,
) -> list[FlowSolverResult]:
    """_summary_

    Args:
        interconnector_data: for each network, contains a list of interconnectors and
            the emissions and generation for each
        region_data: for each region, the emissions and generation

    Returns:
        List of FlowSolverResults for each interconnector with their emissions

    Example arguments:

    interconnector_emissions_and_generated = [
        InterconnectorNetEmissionsEnergy(region_flow=RegionFlow('NSW1->QLD1'), generated_mwh=10.0, emissions_t=1.0),
        ...
    ]

    region_emissions_and_demand = [
        RegionDemandEmissions(region_code=Region('NSW1'), generated_mwh=1000.0, emissions_t=350.0),
        ...
    ]

    Example return:

    [{region_flow: "NSW1->QLD1", emissions: 154.34}, {region_flow: "VIC1->NSW1", emissions: 0.0}, ...]


    Emissions
    """
    a = np.array(
        [
            # emissions balance equations
            [1, 0, 0, 0, 0, 0, 0, 0, -1, 0],
            [0, 1, 0, 0, 0, 0, -1, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0, 0, -1],
            [0, 0, 0, 1, 0, -1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, -1, 1, 1],
            # emissions intensity equations for flow-through regions
            [
                0,
                0,
                0,
                -interconnector_data.get_interconnector(RegionFlow("NSW1->QLD1")).generated_mwh
                / region_data.get_region(Region("NSW1")).generated_mwh,
                0,
                0,
                1,
                0,
                0,
                0,
            ],
            [
                0,
                0,
                0,
                -interconnector_data.get_interconnector(RegionFlow("NSW1->VIC1")).generated_mwh
                / region_data.get_region(Region("NSW1")).generated_mwh,
                0,
                0,
                0,
                1,
                0,
                0,
            ],
            [
                0,
                0,
                0,
                -interconnector_data.get_interconnector(RegionFlow("VIC1->TAS1")).generated_mwh
                / region_data.get_region(Region("VIC1")).generated_mwh,
                0,
                0,
                0,
                0,
                0,
                1,
            ],
            [
                0,
                0,
                0,
                -interconnector_data.get_interconnector(RegionFlow("VIC1->SA1")).generated_mwh
                / region_data.get_region(Region("VIC1")).generated_mwh,
                0,
                0,
                0,
                0,
                1,
                0,
            ],
            [
                0,
                0,
                0,
                -interconnector_data.get_interconnector(RegionFlow("VIC1->NSW1")).generated_mwh
                / region_data.get_region(Region("VIC1")).generated_mwh,
                1,
                0,
                0,
                0,
                0,
                0,
            ],
        ]
    )

    # net emissions for each region (region emissions )
    region_emissions = np.array(
        [
            # net emissions for each region (region emissions, minus exported, plus imported)
            [region_data.get_region(Region("SA1")).emissions_t],
            [region_data.get_region(Region("QLD1")).emissions_t],
            [region_data.get_region(Region("TAS1")).emissions_t],
            [region_data.get_region(Region("NSW1")).emissions_t],
            [region_data.get_region(Region("VIC1")).emissions_t],
            [0],
            [0],
            [0],
            [0],
            [0],
        ]
    )

    # cast nan to 0
    region_emissions = np.nan_to_num(region_emissions)

    # obtain solution
    flow_result = np.linalg.solve(a, region_emissions)

    results = []

    # transform into emission flows
    results.append(FlowSolverResult(region_flow=RegionFlow("NSW1->QLD1"), emissions=flow_result[5][0]))
    results.append(FlowSolverResult(region_flow=RegionFlow("VIC1->NSW1"), emissions=flow_result[6][0]))
    results.append(FlowSolverResult(region_flow=RegionFlow("NSW1->VIC1"), emissions=flow_result[7][0]))
    results.append(FlowSolverResult(region_flow=RegionFlow("VIC1->SA1"), emissions=flow_result[8][0]))
    results.append(FlowSolverResult(region_flow=RegionFlow("VIC1->TAS1"), emissions=flow_result[9][0]))
    results.append(
        FlowSolverResult(
            region_flow=RegionFlow("QLD1->NSW1"),
            emissions=interconnector_data.get_interconnector(RegionFlow("QLD1->NSW1"), default=0).emissions_t,
        )
    )
    results.append(
        FlowSolverResult(
            region_flow=RegionFlow("TAS1->VIC1"),
            emissions=interconnector_data.get_interconnector(RegionFlow("TAS1->VIC1"), default=0).emissions_t,
        )
    )
    results.append(
        FlowSolverResult(
            region_flow=RegionFlow("SA1->VIC1"),
            emissions=interconnector_data.get_interconnector(RegionFlow("SA1->VIC1"), default=0).emissions_t,
        )
    )

    return results


# debugger entry point
if __name__ == "__main__":
    from datetime import datetime

    from tests.core.flow_solver import load_energy_and_emissions_spreadsheet, load_interconnector_interval_spreadsheet

    interval = datetime.fromisoformat("2023-04-09T10:15:00+10:00")

    interconnector_intervals = load_interconnector_interval_spreadsheet(interval=interval)
    energy_and_emissions = load_energy_and_emissions_spreadsheet(interval=interval)

    flows_df = solve_flow_emissions_for_interval(energy_and_emissions, interconnector_intervals)
