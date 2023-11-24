#!/usr/bin/env python
import logging
from datetime import datetime

from opennem.aggregates.facility_daily import (
    run_aggregates_facility_year,
)
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkWEM

logger = logging.getLogger("opennem.catchup")

CURRENT_YEAR = datetime.now().year


def catchup() -> None:
    for network in [NetworkNEM, NetworkAEMORooftop, NetworkAPVI, NetworkWEM]:
        run_aggregates_facility_year(year=CURRENT_YEAR, network=network)

    export_energy(latest=True)
    export_power()

    # run exports for all
    export_map = get_export_map()
    energy_exports = export_map.get_by_stat_type(StatType.energy).get_by_priority(PriorityType.monthly)
    export_energy(energy_exports.resources)


if __name__ == "__main__":
    catchup()
