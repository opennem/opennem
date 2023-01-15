"""
Runs daily export task JSONs for OpenNEM website
"""


import logging
from datetime import datetime, timedelta

from opennem import settings
from opennem.aggregates.facility_daily import run_aggregate_facility_all_by_year, run_aggregates_facility_year
from opennem.aggregates.network_demand import run_aggregates_demand_network
from opennem.aggregates.network_flows import (
    run_emission_update_day,
    run_flow_updates_all_for_network,
    run_flow_updates_all_per_year,
)
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_all_daily, export_all_monthly, export_energy, export_power
from opennem.clients.slack import slack_message
from opennem.db.tasks import refresh_material_views
from opennem.exporter.historic import export_historic_intervals
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkWEM
from opennem.utils.dates import get_today_nem
from opennem.workers.daily_summary import run_daily_fueltech_summary
from opennem.workers.energy import run_energy_calc
from opennem.workers.gap_fill.energy import run_energy_gapfill_for_network

logger = logging.getLogger("opennem.worker.daily")


def energy_runner(days: int = 1) -> None:
    """Energy Runner"""
    dmax = get_today_nem()
    dmin = (dmax - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

    for network in [NetworkNEM, NetworkWEM, NetworkAEMORooftop, NetworkAPVI]:
        run_energy_calc(dmin, dmax, network=network)


def energy_runner_hours(hours: int = 1) -> None:
    """Energy Runner"""
    dmax = get_today_nem().replace(minute=0, second=0, microsecond=0)
    dmin = dmax - timedelta(hours=hours)

    for network in [NetworkNEM, NetworkWEM, NetworkAEMORooftop, NetworkAPVI]:
        run_energy_calc(dmin, dmax, network=network)


def run_export_for_year(year: int, network_region_code: str | None = None) -> None:
    """Run export for latest year"""
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.daily).get_by_year(year)

    if network_region_code:
        energy_exports = energy_exports.get_by_network_region(network_region_code)

    logger.info(f"Running {len(energy_exports.resources)} exports")

    export_energy(energy_exports.resources)


# The actual daily runners


def daily_runner(days: int = 2) -> None:
    """Daily task runner - runs after success of overnight crawls"""
    CURRENT_YEAR = datetime.now().year

    # Energy
    energy_runner(days=days)

    # aggregates
    # 1. flows
    run_flow_updates_all_per_year(CURRENT_YEAR, 1)

    # 2. facilities
    for network in [NetworkNEM, NetworkWEM, NetworkAEMORooftop, NetworkAPVI]:
        run_aggregates_facility_year(year=CURRENT_YEAR, network=network)

    # 3. network demand
    run_aggregates_demand_network()

    #  flows and flow emissions
    run_emission_update_day(days=days)

    #  feature flag for emissions
    #  this will only refresh views on the old version of flows and emissions
    if not settings.flows_and_emissions_v2:
        for view_name in ["mv_facility_all", "mv_interchange_energy_nem_region", "mv_region_emissions"]:
            refresh_material_views(view_name=view_name)
            slack_message(f"refreshed materizlied views on {settings.env}")

    # 4. Run Exports
    #  run exports for latest year
    export_energy(latest=True)

    #  run exports for last year
    run_export_for_year(CURRENT_YEAR - 1)

    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)
    export_energy(energy_exports.resources)

    # 5. Run and send out the daily fueltech summary
    run_daily_fueltech_summary(network=NetworkNEM)

    # export historic intervals
    for network in [NetworkNEM, NetworkWEM]:
        export_historic_intervals(limit=1, networks=[network])

    export_all_daily()
    export_all_monthly()

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
    daily_runner(days=2)
