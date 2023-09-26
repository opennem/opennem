"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

This feature is enabled behind a feature flag in settings_schema.network_flows_v3

Unit tests are at tests/core/flow_solver.py

Documentation at: https://github.com/opennem/opennem/wiki/Network-Flows

"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import NewType

import numpy as np
import pandas as pd

from opennem.schema.network import NetworkNEM, NetworkSchema

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

    interval: datetime
    region_code: Region
    network: NetworkSchema = NetworkNEM
    energy_mwh: float | None = None
    emissions_t: float = 0.0
    generated_mw: float | None = None

    @property
    def energy(self) -> float:
        """Energy in MWh"""
        if self.energy_mwh:
            return self.energy_mwh

        if self.generated_mw:
            return self.generated_mw / self.network.intervals_per_hour

        raise Exception(f"Could not get energy for {self.network.code} {self.region_code} at {self.interval}")

    @property
    def emissions_intensity(self) -> float:
        """Emissions intensity for the region"""
        return self.emissions_t / self.energy


class NetworkRegionsDemandEmissions:
    """For a network contains a list of regions and the demand and emissions for each
    region.
    """

    def __init__(self, network: NetworkSchema, data: list[RegionDemandEmissions]):
        self.data = data
        self.network = network

    def __repr__(self) -> str:
        return f"<RegionNetEmissionsDemandForNetwork region_code={self.network.code} regions={len(self.data)}>"

    def get_region(self, interval: datetime, region: Region) -> RegionDemandEmissions:
        """Get region by code"""
        region_result = list(filter(lambda x: x.interval == interval and x.region_code == region, self.data))

        if not region_result:
            raise FlowSolverException(f"Region {region} not found in network {self.network.code}")

        return region_result.pop()

    def to_dict(self) -> list[dict]:
        """Return flow results as a dictionary"""
        region_demand_emissions = [
            {
                "region_code": i.region_code,
                "generated_mwh": i.energy_mwh,
                "emissions_t": i.emissions_t,
            }
            for i in self.data
        ]

        return region_demand_emissions

    def to_dataframe(self) -> pd.DataFrame:
        """Get flow solver results as a dataframe"""
        region_demand_emissions = self.to_dict()

        region_df = pd.DataFrame.from_records(region_demand_emissions)

        return region_df


# Interconnector flow generation and emissions structures
@dataclass
class InterconnectorNetEmissionsEnergy:
    """Power for each interconnector

    Power is the sum of the generation of the source region minus the exports
    """

    interval: datetime
    region_flow: RegionFlow
    generated_mw: float
    energy_mwh: float

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

    def get_interconnector(
        self, interval: datetime, region_flow: RegionFlow, default: int = 0
    ) -> InterconnectorNetEmissionsEnergy:
        """Get interconnector by region flow"""
        interconnector_result = list(filter(lambda x: x.interval == interval and x.region_flow == region_flow, self.data))

        if not interconnector_result:
            if default:
                return InterconnectorNetEmissionsEnergy(
                    interval=interval, region_flow=region_flow, energy_mwh=default, generated_mw=default
                )

            avaliable_options = ", ".join([x.region_flow for x in self.data])

            raise FlowSolverException(
                f"Interconnector {interval} {region_flow} not found in network {self.network.code}. Available options: {avaliable_options}"
            )

        if len(interconnector_result) > 1:
            raise FlowSolverException(f"Interconnector {interval} {region_flow} has multiple results")

        return interconnector_result.pop()

    def to_dict(self) -> list[dict]:
        """Return flow results as a dictionary"""
        solver_results = [
            {
                "interconnector_region_from": i.interconnector_region_from,
                "interconnector_region_to": i.interconnector_region_to,
                "generated_mwh": i.energy_mwh,
            }
            for i in self.data
        ]

        return solver_results

    def to_dataframe(self) -> pd.DataFrame:
        """Get flow solver results as a dataframe"""
        interconnector_data = self.to_dict()

        interconnector_df = pd.DataFrame.from_records(interconnector_data)

        return interconnector_df


# Flow solver return class
@dataclass
class FlowSolverResultRecord:
    """ """

    interval: datetime
    region_flow: RegionFlow
    emissions_t: float
    generated_mw: float | None = None
    energy_mwh: float | None = None

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

    def __init__(
        self,
        network: NetworkSchema,
        interconnector_data: NetworkInterconnectorEnergyEmissions,
        region_data: NetworkRegionsDemandEmissions,
        result_data: list[FlowSolverResultRecord] | None = None,
    ):
        self.network = network
        self.interconnector_data = interconnector_data
        self.region_data = region_data
        self.data = result_data or []

    def __repr__(self) -> str:
        return f"<FlowSolver network={self.network.code if self.network else ''} results={len(self.data)}>"

    def get_flow(self, interval: datetime, region_flow: RegionFlow, default: int = 0) -> FlowSolverResultRecord:
        """Get flow by region flow"""
        flow_result = list(filter(lambda x: x.region_flow == region_flow, self.data))

        if not flow_result:
            if default:
                return FlowSolverResultRecord(
                    interval=interval, region_flow=region_flow, emissions_t=default, generated_mw=default, energy_mwh=default
                )

            avaliable_options = ", ".join([x.region_flow for x in self.data])

            raise FlowSolverException(f"Flow {interval} interval {region_flow} not found. Available options: {avaliable_options}")

        return flow_result.pop()

    def calculate_flow(self, interval: datetime, region_flow: RegionFlow) -> None:
        """Adds a flow result"""
        interconnector = self.interconnector_data.get_interconnector(interval=interval, region_flow=region_flow)
        region_source = self.region_data.get_region(interval=interval, region=Region(interconnector.interconnector_region_from))

        emissions_t = interconnector.energy_mwh * region_source.emissions_intensity

        flow_result = FlowSolverResultRecord(
            interval=interval,
            region_flow=region_flow,
            emissions_t=emissions_t,
        )

        self.data.append(flow_result)

    def append_flow(self, flow_result: FlowSolverResultRecord) -> None:
        """Adds a flow result"""
        self.data.append(flow_result)

    def append_results(self, flow_results: list[FlowSolverResultRecord]) -> None:
        """Adds a list of flow results"""
        self.data.extend(flow_results)

    def to_dict(self) -> list[dict]:
        """Return flow results as a dictionary"""
        solver_results = [
            {
                "trading_interval": i.interval.replace(tzinfo=None),
                "interconnector_region_from": i.interconnector_region_from,
                "interconnector_region_to": i.interconnector_region_to,
                "emissions": i.emissions_t,
            }
            for i in self.data
        ]

        return solver_results

    def to_dataframe(self) -> pd.DataFrame:
        """Get flow solver results as a dataframe"""
        solver_results = self.to_dict()

        flow_emissions_df = pd.DataFrame.from_records(solver_results)

        return flow_emissions_df


def solve_flow_emissions_with_pandas(interconnector_data, region_data):
    """
    Replace the original solve_flow_emissions_for_interval method with a pandas-based calculation.
    This is a simplified example and assumes that interconnector_data and region_data are pandas DataFrames.
    """
    # Perform your calculations here using pandas DataFrame operations
    # For example, let's assume we want to calculate net emissions for each region
    # Check if 'region' column exists in both DataFrames

    # if "network_region" not in interconnector_data.columns or "network_region" not in region_data.columns:
    #     raise KeyError("Column 'network_region' not found in one or both DataFrames.")

    # # Check if DataFrames are empty
    # if interconnector_data.empty or region_data.empty:
    #     raise ValueError("One or both DataFrames are empty.")

    region_intensities = region_data[["trading_interval", "network_region", "emissions_intensity"]]
    result_set = (
        interconnector_data.merge(
            region_intensities,
            how="inner",
            left_on=["trading_interval", "interconnector_region_to"],
            right_on=["trading_interval", "network_region"],
        )
        .merge(
            region_intensities,
            how="inner",
            left_on=["trading_interval", "interconnector_region_from"],
            right_on=["trading_interval", "network_region"],
            suffixes=("_imports", "_exports"),
        )
        .drop(["interconnector_region_to", "interconnector_region_from", "generated"], axis=1)
    )
    result_set["emissions_import"] = result_set["emissions_intensity_imports"] * result_set["energy"]
    result_set["emissions_exports"] = result_set["emissions_intensity_exports"] * result_set["energy"]
    result_set.drop(["emissions_intensity_imports", "emissions_intensity_exports"], axis=1, inplace=True)

    # old
    exports = pd.DataFrame(
        interconnector_data.copy()
        .rename(columns={"interconnector_region_from": "network_region"})
        .groupby(["trading_interval", "network_region"])["energy"]
        .sum()
    ).rename(columns={"energy": "energy_exports"})
    imports = pd.DataFrame(
        interconnector_data.copy()
        .rename(columns={"interconnector_region_to": "network_region"})
        .groupby(["trading_interval", "network_region"])["energy"]
        .sum()
    ).rename(columns={"energy": "energy_imports"})
    imports_and_exports = exports.merge(imports, left_index=True, right_index=True)

    imports_and_exports.merge(
        result_set.groupby(["trading_interval", "network_region_imports"])["emissions_import"]
        .sum()
        .reset_index()
        .rename({"network_region_imports": "network_region"}, axis=1),
        left_index=True,
        right_on=["trading_interval", "network_region"],
    ).merge(
        result_set.groupby(["trading_interval", "network_region_exports"])["emissions_export"]
        .sum()
        .reset_index()
        .rename({"network_region_imports": "network_region"}, axis=1),
        left_index=True,
        right_on=["trading_interval", "network_region"],
    )

    all_data = imports_and_exports.merge(
        region_data.set_index(["trading_interval", "network_region"])["emissions_intensity"], left_index=True, right_index=True
    )

    # do exports
    all_data["emissions_exports"] = all_data["emissions_intensity"] * all_data["energy_exports"]

    # do imports

    pd.DataFrame(
        interconnector_data.copy()
        .rename({"interconnector_data_to": "network_region"})
        .groupby(["trading_interval", "network_region"])["energy"]
        .sum()
    )

    net_emissions = interconnector_data.groupby("region")["emissions"].sum() - region_data.groupby("region")["emissions"].sum()
    return net_emissions.reset_index()


def solve_flow_emissions_for_interval(
    network: NetworkSchema,
    interval: datetime,
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

    if network.code != "NEM":
        raise FlowSolverException(f"Flow solver only supports NEM network. {network.code} provided")

    region_flow_set = [
        RegionFlow("VIC1->NSW1"),
        RegionFlow("VIC1->TAS1"),
        RegionFlow("VIC1->SA1"),
        RegionFlow("NSW1->VIC1"),
        RegionFlow("NSW1->QLD1"),
        RegionFlow("QLD1->NSW1"),
        RegionFlow("TAS1->VIC1"),
        RegionFlow("SA1->VIC1"),
    ]

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
                -interconnector_data.get_interconnector(interval=interval, region_flow=RegionFlow("NSW1->QLD1")).energy_mwh
                / region_data.get_region(interval=interval, region=Region("NSW1")).energy,
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
                -interconnector_data.get_interconnector(interval=interval, region_flow=RegionFlow("NSW1->VIC1")).energy_mwh
                / region_data.get_region(interval=interval, region=Region("NSW1")).energy,
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
                -interconnector_data.get_interconnector(interval=interval, region_flow=RegionFlow("VIC1->TAS1")).energy_mwh
                / region_data.get_region(interval=interval, region=Region("VIC1")).energy,
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
                -interconnector_data.get_interconnector(interval=interval, region_flow=RegionFlow("VIC1->SA1")).energy_mwh
                / region_data.get_region(interval=interval, region=Region("VIC1")).energy,
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
                -interconnector_data.get_interconnector(interval=interval, region_flow=RegionFlow("VIC1->NSW1")).energy_mwh
                / region_data.get_region(interval=interval, region=Region("VIC1")).energy,
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
            [region_data.get_region(interval=interval, region=Region("SA1")).emissions_t],
            [region_data.get_region(interval=interval, region=Region("QLD1")).emissions_t],
            [region_data.get_region(interval=interval, region=Region("TAS1")).emissions_t],
            [region_data.get_region(interval=interval, region=Region("NSW1")).emissions_t],
            [region_data.get_region(interval=interval, region=Region("VIC1")).emissions_t],
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
    np.linalg.solve(a, region_emissions)

    flow_results = FlowSolverResult(network=network, interconnector_data=interconnector_data, region_data=region_data)

    # simple flows
    for region_flow in region_flow_set:
        flow_results.calculate_flow(interval=interval, region_flow=region_flow)

    return flow_results


def solve_flow_emissions_for_interval_range(
    network: NetworkSchema,
    interconnector_data: NetworkInterconnectorEnergyEmissions,
    region_data: NetworkRegionsDemandEmissions,
) -> FlowSolverResult:
    """
    Solve flow emissions for interval range
    """

    if network.code != "NEM":
        raise FlowSolverException(f"Flow solver only supports NEM network. {network.code} provided")

    intervals = list({i.interval for i in interconnector_data.data})

    logger.debug(f"Called with {len(intervals)} intervals")

    flow_results = FlowSolverResult(network=network, interconnector_data=interconnector_data, region_data=region_data)

    for interval in intervals:
        result_data = solve_flow_emissions_for_interval(
            network=network, interval=interval, interconnector_data=interconnector_data, region_data=region_data
        )
        flow_results.append_results(result_data.data)

    return flow_results


# debugger entry point
if __name__ == "__main__":
    pass
