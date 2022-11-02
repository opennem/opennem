""" Runs all aggregates """

from opennem.aggregates.facility_daily import run_aggregate_facility_days
from opennem.aggregates.network_demand import run_aggregates_demand_network_days
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkWEM


def run_aggregates_all_days(days: int = 1) -> None:
    """Runs all aggregates for all networks back to days"""
    for network in [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop]:
        run_aggregate_facility_days(days=days, network=network)

    run_aggregates_demand_network_days(days=days)
