#!/usr/bin/env python
"""
Script for methods to run for fixtures
"""
import logging
from datetime import datetime

from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.exporter.historic import export_historic_for_year_and_week_no
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_current_week_for_network

logger = logging.getLogger("opennem.scripts.fixtures")


# get week number for last week
CURRENT_WEEK = get_current_week_for_network(network=NetworkNEM)
CURRENT_YEAR = datetime.now().year

WEEK_TO_FETCH = CURRENT_WEEK - 1 if CURRENT_WEEK > 1 else 52


def export_historic_weekly() -> None:
    export_historic_for_year_and_week_no(CURRENT_YEAR, WEEK_TO_FETCH, [NetworkNEM])


def export_energy_all() -> None:
    """Export all energy data"""
    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)
    export_energy(energy_exports.resources)


def export_energy_current_year() -> None:
    """Export energy data for current year"""
    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.daily).get_by_year(CURRENT_YEAR)
    export_energy(energy_exports.resources)


def refresh_fixtures() -> None:
    """this is triggered from ./scripts/refresh_fixtures.sh"""
    export_historic_weekly()
    export_power(latest=True)
    export_energy_all()
    export_energy_current_year()


if __name__ == "__main__":
    refresh_fixtures()
