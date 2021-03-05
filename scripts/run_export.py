#!/usr/bin/env python
"""
Scratchpad to export JSON's for unit tests + testing
"""

from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power


def run_tests() -> None:
    export_map = get_export_map()

    power = (
        export_map.get_by_network_id("NEM")
        .get_by_stat_type(StatType.power)
        .get_by_network_region("VIC1")
        .get_by_priority(PriorityType.live)
    )

    export_power(power.resources)

    energy_map = (
        export_map.get_by_network_id("NEM")
        .get_by_stat_type(StatType.energy)
        .get_by_priority(PriorityType.daily)
        .get_by_network_region("NSW1")
        .get_by_years([2021])
    )

    if len(energy_map.resources):
        export_energy(energy_map.resources)

    energy_map = (
        export_map.get_by_network_id("NEM")
        .get_by_stat_type(StatType.energy)
        .get_by_priority(PriorityType.monthly)
        .get_by_network_region("NSW1")
    )

    if len(energy_map.resources):
        export_energy(energy_map.resources)


if __name__ == "__main__":
    run_tests()
