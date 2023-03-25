"""OpenNEM Network Flows v2

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

"""

import logging

import pandas as pd

# from opennem.db import get_database_engine
# from opennem.db.bulk_insert_csv import build_insert_query, generate_csv_from_records
# from opennem.db.models.opennem import AggregateNetworkFlows
# from opennem.queries.flows import get_interconnector_intervals_query
# from opennem.schema.network import NetworkNEM, NetworkSchema
# from opennem import settings

# from datetime import datetime, timedelta


# from opennem.utils.dates import get_last_complete_day_for_network, get_last_completed_interval_for_network, is_aware

logger = logging.getLogger("opennem.aggregates.flows_v3")


def calculate_flow_for_interval(df_energy_and_emissions: pd.DataFrame, df_interconnector: pd.DataFrame) -> pd.DataFrame:
    """Calculate the flow for a given interval

    df_energy_and_emissions:
        generation and emissions data for each network region
            - energy (MWh)
            - emissions (tCO2)
    df_interconnector:
        interconnector data for each regional flow direction energy that is
            - energy (MWh)

    returns
        a dataframe for each region with the following columns
            - emissions imported (tCO2)
            - emissions exported (tCO2)

    """
    pass


if __name__ == "__main__":
    pass
