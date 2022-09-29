"""
Runs daily export task JSONs for OpenNEM website
"""


import logging
from datetime import datetime

from opennem import settings
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_all_daily, export_all_monthly, export_energy, export_power
from opennem.exporter.historic import export_historic_intervals
from opennem.notifications.slack import slack_message
from opennem.schema.network import NetworkNEM, NetworkWEM
from opennem.workers.aggregates import run_aggregates_all, run_aggregates_all_days, run_aggregates_demand_network
from opennem.workers.emissions import (
    run_emission_update_day,
    run_flow_updates_all_for_network,
    run_flow_updates_all_per_year,
)
from opennem.workers.gap_fill.energy import run_energy_gapfill

logger = logging.getLogger("opennem.worker.daily")


def daily_runner(days: int = 2) -> None:
    """Daily task runner - runs after success of overnight crawls"""
    run_energy_gapfill(days=days)
    run_flow_updates_all_per_year(datetime.now().year, 1)
    run_emission_update_day(days=days)
    run_aggregates_all_days(days=days)

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

    # send a slack message when done
    slack_message(f"Ran daily_runner on {settings.env}")


def all_runner() -> None:
    """Like the daily runner but refreshes all tasks"""
    run_energy_gapfill(days=365)

    # populates the aggregate tables
    run_flow_updates_all_for_network(network=NetworkNEM)
    run_emission_update_day(days=365)
    run_aggregates_all()

    # run the exports for all
    export_power(latest=False)
    export_energy(latest=False)

    export_all_daily()
    export_all_monthly()

    # send slack message when done
    slack_message(f"ran all_runner on {settings.env}")


if __name__ == "__main__":
    daily_runner()
