"""
Runs daily export task JSONs for OpenNEM website
"""


import logging
from datetime import datetime

from opennem import settings
from opennem.aggregates.facility_daily import run_aggregate_facility_all_by_year, run_aggregates_facility_year
from opennem.aggregates.network_demand import run_aggregates_demand_network
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_all_daily, export_all_monthly, export_energy, export_power
from opennem.db.tasks import refresh_material_views
from opennem.exporter.historic import export_historic_intervals
from opennem.notifications.slack import slack_message
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkWEM
from opennem.workers.daily_summary import run_daily_fueltech_summary
from opennem.workers.emissions import (
    run_emission_update_day,
    run_flow_updates_all_for_network,
    run_flow_updates_all_per_year,
)
from opennem.workers.gap_fill.energy import run_energy_gapfill_for_network, run_energy_gapfill_for_network_by_days

logger = logging.getLogger("opennem.worker.daily")


def daily_runner(days: int = 2) -> None:
    """Daily task runner - runs after success of overnight crawls"""
    CURRENT_YEAR = datetime.now().year

    run_energy_gapfill_for_network_by_days(days=days)

    # aggregates
    # 1. flows
    run_flow_updates_all_per_year(CURRENT_YEAR, 1)

    # 2. facilities
    for network in [NetworkNEM, NetworkWEM, NetworkAEMORooftop, NetworkAPVI]:
        run_aggregates_facility_year(year=CURRENT_YEAR, network=network)

    # 3. network demand
    run_aggregates_demand_network()

    # flows and flow emissions
    run_emission_update_day(days=days)

    # feature flag for emissions
    if not settings.flows_and_emissions_v2:
        for view_name in ["mv_facility_all", "mv_interchange_energy_nem_region", "mv_region_emissions"]:
            refresh_material_views(view_name=view_name)

    # run exports for latest year
    export_energy(latest=True)

    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)
    export_energy(energy_exports.resources)

    # export historic intervals
    for network in [NetworkNEM, NetworkWEM]:
        export_historic_intervals(limit=1, networks=[network])

    export_all_daily()
    export_all_monthly()

    # Skip if we're not on prod
    if settings.env == "production":
        run_daily_fueltech_summary(network=NetworkNEM)

    run_daily_fueltech_summary(network=NetworkNEM)

    # send a slack message when done
    slack_message(f"Ran daily_runner on {settings.env}")


def all_runner() -> None:
    """Like the daily runner but refreshes all tasks"""
    run_energy_gapfill_for_network(network=NetworkNEM)

    # populates the aggregate tables
    run_flow_updates_all_for_network(network=NetworkNEM)

    for network in [NetworkNEM, NetworkWEM, NetworkAEMORooftop, NetworkAPVI]:
        run_aggregate_facility_all_by_year(network=network)

    # run the exports for all
    export_power(latest=False)
    export_energy(latest=False)

    export_all_daily()
    export_all_monthly()

    # send slack message when done
    slack_message(f"ran all_runner on {settings.env}")


if __name__ == "__main__":
    all_runner()
