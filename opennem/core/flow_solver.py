"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

This feature is enabled behind a feature flag in settings_schema.network_flows_v3

Unit tests are at tests/core/flow_solver.py

Documentation at: https://github.com/opennem/opennem/wiki/Network-Flows

"""

import logging

import pandas as pd

from opennem.schema.network import NetworkNEM, NetworkSchema

logger = logging.getLogger("opennem.core.flow_solver")


def solve_flow_emissions_with_pandas(interconnector_data, region_data, network: NetworkSchema = NetworkNEM) -> pd.DataFrame:
    """ """
    region_intensities = region_data[["interval", "network_region", "emissions_intensity"]]
    result_set = interconnector_data.merge(
        region_intensities,
        how="inner",
        left_on=["interval", "interconnector_region_to"],
        right_on=["interval", "network_region"],
    ).merge(
        region_intensities,
        how="inner",
        left_on=["interval", "interconnector_region_from"],
        right_on=["interval", "network_region"],
        suffixes=["_imports", "_exports"],
    )
    result_set["flow"] = result_set["interconnector_region_from"] + "->" + result_set["interconnector_region_to"]
    result_set["emissions"] = result_set["emissions_intensity_exports"] * result_set["energy"]
    result_set.drop(
        [
            # "interconnector_region_to",
            # "interconnector_region_from",
            "generated",
            "network_region_exports",
            "network_region_imports",
            "emissions_intensity_imports",
            "emissions_intensity_exports",
        ],
        axis=1,
        inplace=True,
    )

    # group into import and export dataframes
    imports = (
        (
            result_set.groupby(["interval", "interconnector_region_to"])[["energy", "emissions"]].apply(
                lambda x: x.astype(float).sum()
            )
        )
        .reset_index()
        .rename(
            {
                "interconnector_region_to": "network_region",
                "energy": "energy_imports",
                "emissions": "emissions_imports",
            },
            axis=1,
        )
        .set_index(["interval", "network_region"])
    )

    exports = (
        (
            result_set.groupby(["interval", "interconnector_region_from"])[["energy", "emissions"]].apply(
                lambda x: x.astype(float).sum()
            )
        )
        .reset_index()
        .rename(
            {
                "interconnector_region_from": "network_region",
                "energy": "energy_exports",
                "emissions": "emissions_exports",
            },
            axis=1,
        )
        .set_index(["interval", "network_region"])
    )

    # merge into single dataframe
    result_data = imports.merge(exports, left_index=True, right_index=True)

    # Clean up the rest of the data
    result_data["market_value_exports"] = 0.0
    result_data["market_value_imports"] = 0.0
    result_data["network_id"] = network.code
    result_data.fillna(0, inplace=True)

    # fix timezone
    # result_data.index.levels[0].tz_localize(network.get_fixed_offset())
    result_data.reset_index(inplace=True)

    return result_data


# debugger entry point
if __name__ == "__main__":
    pass
