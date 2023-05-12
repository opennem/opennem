"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger("opennem.core.flow_solver")


def calculate_flow_for_interval(df_energy_and_emissions: pd.DataFrame, df_interconnector: pd.DataFrame) -> pd.DataFrame:
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
    regions = df_energy_and_emissions["network_region"].unique()
    region_map = {region: i for i, region in enumerate(regions)}

    # Create energy and emission matrices
    energy_matrix = np.zeros((len(regions), len(regions)))
    emissions_matrix = np.zeros((len(regions), len(regions)))

    for _, row in df_interconnector.iterrows():
        from_region = row["interconnector_region_from"]
        to_region = row["interconnector_region_to"]
        energy = row["energy"]

        if energy > 0:  # energy exported
            energy_matrix[region_map[from_region]][region_map[to_region]] = energy
        else:  # energy imported
            energy_matrix[region_map[to_region]][region_map[from_region]] = -energy

    # Solve for emission flows using emissions intensity and energy flows
    emissions_intensity = np.array(df_energy_and_emissions["emissions"] / df_energy_and_emissions["energy"])

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


if __name__ == "__main__":
    pass
