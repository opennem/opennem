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
import pandas as pd

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
        region_result = list(filter(lambda x: x.region_code == region_code, self.data))

        if not region_result:
            raise FlowSolverException(f"Region {region_code} not found in network {self.network.code}")

        return region_result.pop()


# Interconnector flow generation and emissions structures
@dataclass
class InterconnectorNetEmissionsEnergy:
    """Power for each interconnector

    Power is the sum of the generation of the source region minus the exports
    """

    region_flow: RegionFlow
    generated_mwh: float

    @property
    def interconnector_region_from(self) -> str:
        """Region code for the interconnector source"""
        return self.region_flow.split("->")[0]

    @property
    def interconnector_region_to(self) -> str:
        """Region code for the interconnector destination"""
        return self.region_flow.split("->")[1]


class NetworkInterconnectorEnergyEmissions:
    """For a network contains a list of interconnectors and the emissions and generation for each"""

    def __init__(self, network: NetworkSchema, data: list[InterconnectorNetEmissionsEnergy]):
        self.data = data
        self.network = network

    def get_interconnector(self, region_flow: RegionFlow, default: int = 0) -> InterconnectorNetEmissionsEnergy:
        """Get interconnector by region flow"""
        interconnector_result = list(filter(lambda x: x.region_flow == region_flow, self.data))

        if not interconnector_result:
            if default:
                return InterconnectorNetEmissionsEnergy(region_flow=region_flow, generated_mwh=default)

            avaliable_options = ", ".join([x.region_flow for x in self.data])

            raise FlowSolverException(
                f"Interconnector {region_flow} not found in network {self.network.code}. Available options: {avaliable_options}"
            )

        return interconnector_result.pop()


# Flow solver return class
@dataclass
class FlowSolverResultRecord:
    """ """

    region_flow: RegionFlow
    emissions_t: float

    @property
    def interconnector_region_from(self) -> str:
        """Region code for the interconnector source"""
        return self.region_flow.split("->")[0]

    @property
    def interconnector_region_to(self) -> str:
        """Region code for the interconnector destination"""
        return self.region_flow.split("->")[1]


class FlowSolverResult:
    """Class to store flow solver results"""

    def __init__(self, data: list[FlowSolverResultRecord], network: NetworkSchema | None = None):
        self.network = network
        self.data = data

    def __repr__(self) -> str:
        return f"<FlowSolver network={self.network.code} results={len(self.data)}>"

    def get_flow(self, region_flow: RegionFlow, default: int = 0) -> FlowSolverResultRecord:
        """Get flow by region flow"""
        flow_result = list(filter(lambda x: x.region_flow == region_flow, self.data))

        if not flow_result:
            if default:
                return FlowSolverResultRecord(region_flow=region_flow, emissions_t=default)

            avaliable_options = ", ".join([x.region_flow for x in self.data])

            raise FlowSolverException(f"Flow {region_flow} not found. Available options: {avaliable_options}")

        return flow_result.pop()

    def to_dict(self) -> list[dict]:
        """Return flow results as a dictionary"""
        solver_results = [
            {
                "trading_interval": interval.replace(tzinfo=None),
                "interconnector_region_from": i.interconnector_region_from,
                "interconnector_region_to": i.interconnector_region_to,
                "emissions": i.emissions_t,
            }
            for i in self.data
        ]

        return solver_results

    def get_dataframe(self) -> pd.DataFrame:
        """Get flow solver results as a dataframe"""
        solver_results = self.to_dict()

        flow_emissions_df = pd.DataFrame.from_records(solver_results)

        return flow_emissions_df


def solve_flow_emissions_for_interval(
    interconnector_data: NetworkInterconnectorEnergyEmissions,
    region_data: NetworkRegionsDemandEmissions,
) -> FlowSolverResult:
    """_summary_

    Args:
        interconnector_data: for each network, contains a list of interconnectors and
            the emissions and generation for each
        region_data: for each region, the emissions and generation

    Returns:
        List of FlowSolverResults for each interconnector with their emissions

    Example arguments:

    interconnector_data = [
        InterconnectorNetEmissionsEnergy(region_flow=RegionFlow('NSW1->QLD1'), generated_mwh=10.0, emissions_t=1.0),
        ...
    ]

    region_data = [
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
    results.append(FlowSolverResultRecord(region_flow=RegionFlow("NSW1->QLD1"), emissions_t=flow_result[5][0]))
    results.append(FlowSolverResultRecord(region_flow=RegionFlow("VIC1->NSW1"), emissions_t=flow_result[6][0]))
    results.append(FlowSolverResultRecord(region_flow=RegionFlow("NSW1->VIC1"), emissions_t=flow_result[7][0]))
    results.append(FlowSolverResultRecord(region_flow=RegionFlow("VIC1->SA1"), emissions_t=flow_result[8][0]))
    results.append(FlowSolverResultRecord(region_flow=RegionFlow("VIC1->TAS1"), emissions_t=flow_result[9][0]))
    # simple flows
    results.append(
        FlowSolverResultRecord(
            region_flow=RegionFlow("QLD1->NSW1"),
            emissions_t=region_data.get_region(Region("QLD1")).emissions_t,
        )
    )
    results.append(
        FlowSolverResultRecord(
            region_flow=RegionFlow("TAS1->VIC1"),
            emissions_t=region_data.get_region(Region("TAS1")).emissions_t,
        )
    )
    results.append(
        FlowSolverResultRecord(
            region_flow=RegionFlow("SA1->VIC1"),
            emissions_t=region_data.get_region(Region("SA1")).emissions_t,
        )
    )

    response_model = FlowSolverResult(data=results)

    return response_model


# debugger entry point
if __name__ == "__main__":
    from datetime import datetime

    from tests.core.flow_solver import load_energy_and_emissions_spreadsheet, load_interconnector_interval_spreadsheet

    interval = datetime.fromisoformat("2023-04-09T10:15:00+10:00")

    interconnector_intervals = load_interconnector_interval_spreadsheet(interval=interval)
    energy_and_emissions = load_energy_and_emissions_spreadsheet(interval=interval)

    flows_df = solve_flow_emissions_for_interval(energy_and_emissions, interconnector_intervals)
