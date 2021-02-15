#!/usr/bin/env python
"""
Scratchpad to export JSON's for unit tests + testing
"""

from opennem.api.export.map import PriorityType, StatExport, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power


def run_tests() -> None:
    # network_schema = network_from_network_code("NEM")
    # scada_range = get_scada_range(network=network_schema)
    # bom_station = get_network_region_weather_station("NEM")

    export_map = get_export_map()

    # nem_energy = (
    #     export_map.get_by_network_id("NEM")
    #     .get_by_stat_type(StatType.energy)
    #     .get_by_priority(PriorityType.daily)
    #     .get_by_network_region("NSW1")
    #     .get_by_years([2020, 2021])
    # )

    # if len(nem_energy.resources):
    #     export_energy(nem_energy.resources)

    nem_power = (
        export_map.get_by_network_id("WEM")
        .get_by_stat_type(StatType.power)
        .get_by_priority(PriorityType.live)
    )

    export_power(nem_power.resources)


if __name__ == "__main__":
    run_tests()
