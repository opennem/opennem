"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

This feature is enabled behind a feature flag in settings_schema.network_flows_v3

Unit tests are at tests/core/flow_solver.py

Documentation at: https://github.com/opennem/opennem/wiki/Network-Flows

"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger("opennem.core.flow_solver")


def calculate_total_import_and_export_per_region_for_interval(interconnector_data: pd.DataFrame) -> pd.DataFrame:
    """Calculates total import and export energy for a region using the interconnector dataframe

    Args:
        interconnector_data (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: total imports and export for each region for each interval

    Example return dataframe:

                                energy_imports  energy_exports
    network_id  network_region
    NEM         NSW1                      82.5             0.0
                QLD1                       0.0            55.0
                SA1                       22.0             0.0
                TAS1                       0.0            11.0
                VIC1                      11.0            49.5
    """

    dx = interconnector_data.groupby(["interconnector_region_from", "interconnector_region_to"]).energy.sum().reset_index()

    # invert regions
    dy = dx.rename(
        columns={
            "interconnector_region_from": "interconnector_region_to",
            "interconnector_region_to": "interconnector_region_from",
        }
    )

    # set indexes
    dy.set_index(["interconnector_region_to", "interconnector_region_from"], inplace=True)
    dx.set_index(["interconnector_region_to", "interconnector_region_from"], inplace=True)

    dy["energy"] *= -1

    dx.loc[dx.energy < 0, "energy"] = 0
    dy.loc[dy.energy < 0, "energy"] = 0

    f = pd.concat([dx, dy])

    energy_flows = pd.DataFrame(
        {
            "energy_imports": f.groupby("interconnector_region_to").energy.sum(),
            "energy_exports": f.groupby("interconnector_region_from").energy.sum(),
        }
    )

    energy_flows["network_id"] = "NEM"

    energy_flows.reset_index(inplace=True)
    energy_flows.rename(columns={"index": "network_region"}, inplace=True)
    energy_flows.set_index(["network_id", "network_region"], inplace=True)

    return energy_flows


def calculate_demand_region_for_interval() -> pd.DataFrame:
    """ """
    pass


def calculate_flow_for_interval(energy_and_emissions: pd.DataFrame, interconnector: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the flow of energy and emissions between network regions for a given interval.

    Arguments:
    df_energy_and_emissions: pd.DataFrame
        A DataFrame containing the energy generation and emissions data for each network region.
        The DataFrame has the following columns:
        - 'trading_interval': datetime object indicating the time interval.
        - 'network_id': string indicating the network id.
        - 'network_region': string indicating the network region id.
        - 'energy': float indicating the energy generated (in MWh) in the region.
        - 'emissions': float indicating the emissions (in tCO2) from the region.
        - 'emissions_intensity': float indicating the emissions intensity (tCO2/MWh).

    df_interconnector: pd.DataFrame
        A DataFrame containing the interconnector data for each regional flow direction energy.
        The DataFrame has the following columns:
        - 'trading_interval': datetime object indicating the time interval.
        - 'network_id': string indicating the network id.
        - 'interconnector_region_from': string indicating the id of the region exporting energy.
        - 'interconnector_region_to': string indicating the id of the region importing energy.
        - 'energy': float indicating the energy transferred (in MWh) between the regions.

    Returns:
    pd.DataFrame
        A DataFrame containing the energy and emissions flow data for each region.
        The DataFrame has the following columns:
        - 'network_region': string indicating the network region id.
        - 'energy_exported': float indicating the total energy exported (in MWh) from the region.
        - 'energy_imported': float indicating the total energy imported (in MWh) to the region.
        - 'emissions_exported': float indicating the total emissions exported (in tCO2) from the region.
        - 'emissions_imported': float indicating the total emissions imported (in tCO2) to the region.
    """
    # Create a mapping of regions to indices for easier matrix manipulation
    regions = energy_and_emissions["network_region"].unique()
    region_map = {region: i for i, region in enumerate(regions)}

    # Create energy and emission matrices
    energy_matrix = np.zeros((len(regions), len(regions)))
    emissions_matrix = np.zeros((len(regions), len(regions)))

    # Populate energy matrix

    # Populate flow matrix
    calculate_total_import_and_export_per_region_for_interval(interconnector_data=interconnector)

    for _, row in interconnector.iterrows():
        from_region = row["interconnector_region_from"]
        to_region = row["interconnector_region_to"]
        energy = row["energy"]

        if energy > 0:  # energy exported
            energy_matrix[region_map[from_region]][region_map[to_region]] = energy
        else:  # energy imported
            energy_matrix[region_map[to_region]][region_map[from_region]] = -energy

    # Solve for emission flows using emissions intensity and energy flows
    emissions_intensity = np.array(energy_and_emissions["emissions"] / energy_and_emissions["energy"])

    assert max(emissions_intensity) <= 1700, "Emissions intensity is too high"

    emissions_matrix = np.linalg.solve(energy_matrix, energy_matrix * emissions_intensity[:, np.newaxis])

    # Create the output DataFrame
    df_output = pd.DataFrame(
        {
            "network_region": regions,
            "energy_exported": np.sum(energy_matrix, axis=1),
            "energy_imported": np.sum(energy_matrix, axis=0),
            "emissions_exported": np.sum(emissions_matrix, axis=1),
            "emissions_imported": np.sum(emissions_matrix, axis=0),
        }
    )

    assert len(df_output) == len(regions), "Number of regions in results does not match number of regions in input"

    return df_output


def solve_flows_for_interval(emissions_dict=None, power_dict=None, demand_dict=None) -> pd.DataFrame:
    """_summary_

    Args:
        emissions_dict (_type_, optional): _description_. Defaults to None.
        power_dict (_type_, optional): _description_. Defaults to None.
        demand_dict (_type_, optional): _description_. Defaults to None.

    Returns:
        pd.DataFrame: _description_
    """
    a = np.array(
        [
            # emissions balance equations
            [1, 0, 0, 0, 0, 0, 0, 0, -1, 0],
            [0, 1, 0, 0, 0, 0, -1, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0, 0, -1],
            [0, 0, 0, 1, 0, -1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, -1, 1, 1],
            # emissions intensity equations
            [0, 0, 0, -power_dict[("NSW1", "QLD1")] / demand_dict["NSW1"], 0, 0, 1, 0, 0, 0],
            [0, 0, 0, -power_dict[("NSW1", "VIC1")] / demand_dict["NSW1"], 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, -power_dict[("VIC1", "TAS1")] / demand_dict["VIC1"], 0, 0, 0, 0, 1],
            [0, 0, 0, 0, -power_dict[("VIC1", "SA1")] / demand_dict["VIC1"], 0, 0, 0, 1, 0],
            [0, 0, 0, 0, -power_dict[("VIC1", "NSW1")] / demand_dict["VIC1"], 1, 0, 0, 0, 0],
        ]
    )

    b = np.array(
        [
            [emissions_dict["SA1"] - emissions_dict[("SA1", "VIC1")]],
            [emissions_dict["QLD1"] - emissions_dict[("QLD1", "NSW1")]],
            [emissions_dict["TAS1"] - emissions_dict[("TAS1", "VIC1")]],
            [emissions_dict["NSW1"] + emissions_dict[("QLD1", "NSW1")]],
            [emissions_dict["VIC1"] + emissions_dict[("SA1", "VIC1")] + emissions_dict[("TAS1", "VIC1")]],
            [0],
            [0],
            [0],
            [0],
            [0],
        ]
    )

    # cast nan to 0
    b = np.nan_to_num(b)

    # get result
    result = np.linalg.solve(a, b)

    # transform into emission flows
    emission_flows = {
        ("NSW1", "QLD1"): result[6][0],
        ("VIC1", "NSW1"): result[5][0],
        ("NSW1", "VIC1"): result[7][0],
        ("VIC1", "SA1"): result[8][0],
        ("VIC1", "TAS1"): result[9][0],
        ("QLD1", "NSW1"): emissions_dict.get(("QLD1", "NSW1"), 0),
        ("TAS1", "VIC1"): emissions_dict.get(("TAS1", "VIC1"), 0),
        ("SA1", "VIC1"): emissions_dict.get(("SA1", "VIC1"), 0),
    }

    # shape into dataframe
    df = pd.DataFrame.from_dict(emission_flows, orient="index")
    df.columns = ["emissions"]

    # @TODO join import / export energy flows

    df.reset_index(inplace=True)

    return df


# debugger entry point
if __name__ == "__main__":
    from datetime import datetime

    from tests.core.flow_solver import load_energy_and_emissions, load_interconnector_interval

    interval = datetime.fromisoformat("2023-04-09T10:15:00+10:00")

    interconnector_intervals = load_interconnector_interval(interval=interval)
    energy_and_emissions = load_energy_and_emissions(interval=interval)

    flows_df = calculate_flow_for_interval(energy_and_emissions, interconnector_intervals)
