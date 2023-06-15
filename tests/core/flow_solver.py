from datetime import datetime

import pandas as pd
import pytest

from opennem.core.flow_solver import (
    FlowSolverResult,
    InterconnectorNetEmissionsEnergy,
    NetworkInterconnectorEnergyEmissions,
    NetworkRegionsDemandEmissions,
    Region,
    RegionDemandEmissions,
    RegionFlow,
    solve_flow_emissions_for_interval,
)
from opennem.schema.network import NetworkNEM, NetworkSchema


# fixtures for this test adapted from Simons spreadsheet at
# https://docs.google.com/spreadsheets/d/12eAnLYSdXJ55I06m0sRfrJyVd-1gGsSr/edit#gid=1210585319
def load_energy_and_emissions_spreadsheet(interval: datetime, network: NetworkSchema = NetworkNEM) -> pd.DataFrame:
    """Load generation and emissions for an interval and the interval prior for each region of the network

    trading_interval network_id network_region  energy  emissions  emissions_intensity
          2023-01-01        NEM           QLD1     500        325                 0.65
          2023-01-01        NEM           NSW1     600        330                 0.55
          2023-01-01        NEM           VIC1     300        180                 0.60
          2023-01-01        NEM            SA1     100         15                 0.15
          2023-01-01        NEM           TAS1      80          4                 0.05
    """
    df = pd.DataFrame(
        {
            "trading_interval": [interval] * 5,
            "network_id": [network.code] * 5,
            "network_region": ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"],
            "energy": [500, 600, 300, 100, 80],
            "emissions": [325, 330, 180, 15, 4],
        },
    )

    df["emissions_intensity"] = df["emissions"] / df["energy"]

    return df


def load_interconnector_interval_spreadsheet(interval: datetime, network: NetworkSchema = NetworkNEM) -> pd.DataFrame:
    """Load interval for each interconnector for a given interval


    trading_interval network_id interconnector_region_from interconnector_region_to  energy
          2023-01-01        NEM                       VIC1                      SA1    22.0
          2023-01-01        NEM                       NSW1                     QLD1   -55.0
          2023-01-01        NEM                       TAS1                     VIC1    11.0
          2023-01-01        NEM                       VIC1                     NSW1    27.5
    """

    df = pd.DataFrame(
        {
            "trading_interval": [interval] * 4,
            "network_id": [network.code] * 4,
            "interconnector_region_from": ["VIC1", "NSW1", "TAS1", "VIC1"],
            "interconnector_region_to": ["SA1", "QLD1", "VIC1", "NSW1"],
            "energy": [22, -55, 11, 27.5],
        },
    )

    return df


def flow_solver_test_output_spreadsheet() -> pd.DataFrame:
    """This is the test output to compare against

    network_region  energy_exported  emissions_exported  energy_imported emissions_imported
              TAS1             11.0                0.55              0.0                0.0
              VIC1             49.5               28.70             11.0                0.6
               SA1              0.0                0.00             22.0               12.8
              QLD1             55.0               35.75              0.0                0.0
              NSW1              0.0                0.00             82.5               51.7

    """
    df = pd.DataFrame(
        {
            "network_region": ["TAS1", "VIC1", "SA1", "QLD1", "NSW1"],
            "energy_exported": [11, 49.5, 0, 55, 0],
            "emissions_exported": [0.55, 28.7, 0, 35.75, 0],
            "energy_imported": [0, 11, 22, 0, 82.5],
            "emissions_imported": [0, 0.55, 12.8, 0, 51.7],
        },
    )

    return df


# Secondary test of raw values from dicts into solver function


@pytest.mark.parametrize(
    "region_data, interconnector_data, expected_output",
    [
        (
            NetworkRegionsDemandEmissions(
                network=NetworkNEM,
                data=[
                    RegionDemandEmissions(region_code=Region("NSW1"), generated_mwh=99876.21, emissions_t=63576.28),
                    RegionDemandEmissions(region_code=Region("QLD1"), generated_mwh=92799.05, emissions_t=72424.89),
                    RegionDemandEmissions(region_code=Region("SA1"), generated_mwh=14571.28, emissions_t=1207.01),
                    RegionDemandEmissions(region_code=Region("TAS1"), generated_mwh=9635.90, emissions_t=0),
                    RegionDemandEmissions(region_code=Region("VIC1"), generated_mwh=68247.64, emissions_t=55621.22),
                ],
            ),
            NetworkInterconnectorEnergyEmissions(
                network=NetworkNEM,
                data=[
                    InterconnectorNetEmissionsEnergy(region_flow=RegionFlow("QLD1->NSW1"), generated_mwh=1845378.01),
                    InterconnectorNetEmissionsEnergy(region_flow=RegionFlow("TAS1->VIC1"), generated_mwh=9345725.37),
                    InterconnectorNetEmissionsEnergy(region_flow=RegionFlow("SA1->VIC1"), generated_mwh=2263190.02),
                ],
            ),
            [
                FlowSolverResult(region_flow=RegionFlow("NSW1->QLD1"), emissions=0.0002745705239764611),
            ],
        ),
    ],
)
def test_solve_flows_for_interval(
    region_data: NetworkRegionsDemandEmissions, interconnector_data: NetworkInterconnectorEnergyEmissions, expected_output: list
) -> None:
    """
    Unit test for the solve_flows_for_interval function.
    """
    subject_output = solve_flow_emissions_for_interval(region_data=region_data, interconnector_data=interconnector_data)
    assert subject_output == expected_output, "output matches expected output"
