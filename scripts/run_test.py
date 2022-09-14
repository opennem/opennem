#!/usr/bin/env python
import logging
from datetime import datetime

from opennem import settings
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.exporter.historic import export_historic_intervals
from opennem.notifications.slack import slack_message
from opennem.schema.network import NetworkNEM, NetworkWEM
from opennem.workers.aggregates import run_aggregates_all, run_aggregates_all_days, run_aggregates_demand_network
from opennem.workers.emissions import (
    run_emission_update_day,
    run_flow_updates_all_for_nem,
    run_flow_updates_all_per_year,
)
from opennem.workers.gap_fill.energy import run_energy_gapfill

logger = logging.getLogger("opennem.run_test")


def run_export_all() -> None:
    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)
    export_energy(energy_exports.resources)


if __name__ == "__main__":
    run_export_all()
