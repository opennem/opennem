#!/usr/bin/env python
"""
Test scripts for determining price discrepency as detailed in issue:


"""

from opennem.aggregates.facility_daily import run_aggregates_facility_year
from opennem.aggregates.network_demand import run_aggregates_demand_network
from opennem.schema.network import NetworkNEM


def run_aggregates() -> None:
    """First check - re-run the aggregates"""
    run_aggregates_demand_network(networks=[NetworkNEM])

    for year in range(2010, 1998, -1):
        run_aggregates_facility_year(year=year, network=NetworkNEM)


if __name__ == "__main__":
    run_aggregates()
