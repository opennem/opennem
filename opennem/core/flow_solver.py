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

# from result import Err, Ok, Result

logger = logging.getLogger("opennem.core.flow_solver")


class FlowSolverException(Exception):
    pass


# ex. NSW1
Region = NewType("Region", str)

# ex. NSW1->QLD1
RegionFlow = NewType("RegionFlow", str)


@dataclass
class FlowSolverEmissions:
    """Emissions for each region

    Emissions are the sum of the emissions for that region plus the emissions
    of the imports minus the emissions of the exports
    """

    region_code: Region
    emissions: float


@dataclass
class FlowSolverDemand:
    """Demand for each region

    Demand is generation for that region minus exports plus imports
    """

    region_code: Region
    demand: float
    emissions: float


@dataclass
class FlowSolverPower:
    """Power for each interconnector

    Power is the sum of the generation of the source region minus the exports
    """

    region_flow: RegionFlow
    power: float


@dataclass
class FlowSolverResult:
    """ """

    region_flow: RegionFlow
    emissions: float


def solve_flows_for_interval(
    emissions: list[FlowSolverEmissions], power: list[FlowSolverPower], demand: list[FlowSolverDemand]
) -> list[FlowSolverResult]:
    """_summary_

    Args:
        emissions_dict (_type_, optional): _description_. Defaults to None.
        power_dict (_type_, optional): _description_. Defaults to None.
        demand_dict (_type_, optional): _description_. Defaults to None.

    Returns:
        pd.DataFrame: _description_

    @TODO add typed dict params
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
            [0, 0, 0, -power[("NSW1", "QLD1")] / demand["NSW1"], 0, 0, 1, 0, 0, 0],
            [0, 0, 0, -power[("NSW1", "VIC1")] / demand["NSW1"], 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, -power[("VIC1", "TAS1")] / demand["VIC1"], 0, 0, 0, 0, 1],
            [0, 0, 0, 0, -power[("VIC1", "SA1")] / demand["VIC1"], 0, 0, 0, 1, 0],
            [0, 0, 0, 0, -power[("VIC1", "NSW1")] / demand["VIC1"], 1, 0, 0, 0, 0],
        ]
    )

    # net emissions for each region (region emissions )
    region_emissions = np.array(
        [
            [emissions["SA1"] - emissions[("SA1", "VIC1")]],
            [emissions["QLD1"] - emissions[("QLD1", "NSW1")]],
            [emissions["TAS1"] - emissions[("TAS1", "VIC1")]],
            [emissions["NSW1"] + emissions[("QLD1", "NSW1")]],
            [emissions["VIC1"] + emissions[("SA1", "VIC1")] + emissions[("TAS1", "VIC1")]],
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
    result = np.linalg.solve(a, region_emissions)

    # transform into emission flows
    emission_flows = {
        ("NSW1->QLD1"): result[6][0],
        ("VIC1->NSW1"): result[5][0],
        ("NSW1->VIC1"): result[7][0],
        ("VIC1->SA1"): result[8][0],
        ("VIC1->TAS1"): result[9][0],
        ("QLD1->NSW1"): emissions.get(("QLD1->NSW1"), 0),
        ("TAS1->VIC1"): emissions.get(("TAS1->VIC1"), 0),
        ("SA1->VIC1"): emissions.get(("SA1->VIC1"), 0),
    }

    return emission_flows


# debugger entry point
if __name__ == "__main__":
    from datetime import datetime

    from tests.core.flow_solver import load_energy_and_emissions_spreadsheet, load_interconnector_interval_spreadsheet

    interval = datetime.fromisoformat("2023-04-09T10:15:00+10:00")

    interconnector_intervals = load_interconnector_interval_spreadsheet(interval=interval)
    energy_and_emissions = load_energy_and_emissions_spreadsheet(interval=interval)

    flows_df = solve_flows_for_interval(energy_and_emissions, interconnector_intervals)
