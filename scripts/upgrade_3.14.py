#!/usr/bin/env python
""""
This script runs all the upgrade tasks for version 3.14

"""

from opennem.aggregates.facility_daily import run_aggregate_facility_all_by_year
from opennem.aggregates.network_demand import run_aggregates_demand_network
from opennem.aggregates.network_flows import run_flow_updates_all_for_network
from opennem.api.export.tasks import export_all_daily, export_all_monthly, export_energy
from opennem.crawl import run_crawl
from opennem.crawlers.mms import AEMOMMSMeterDataGenDuid
from opennem.importer.db import import_all_facilities
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkOpenNEMRooftopBackfill, NetworkWEM
from scripts.load_historic_dispatch_regionsum import import_dispatch_regionsum


def upgrade_3_14() -> None:
    """Processes to run to upgrade from 3.13 to 3.14"""
    # 0. update all facilities
    import_all_facilities()

    # 1. load historic dispatch
    import_dispatch_regionsum()

    # 2. load MMS data
    run_crawl(AEMOMMSMeterDataGenDuid)

    # 3. run all facility aggregates
    for network in [NetworkNEM, NetworkWEM, NetworkAEMORooftop, NetworkAPVI, NetworkOpenNEMRooftopBackfill]:
        run_aggregate_facility_all_by_year(network=network)

    run_aggregates_demand_network()

    run_flow_updates_all_for_network(network=NetworkNEM)

    # run all exports
    export_energy(latest=False)
    export_all_daily()
    export_all_monthly()


def upgrade_3_14_part_2() -> None:
    """part 2 of upgrade"""
    import_all_facilities()

    for network in [NetworkNEM]:
        run_aggregate_facility_all_by_year(network=network)

    # run all exports
    export_energy(latest=False)
    export_all_daily()
    export_all_monthly()


if __name__ == "__main__":
    upgrade_3_14_part_2()
