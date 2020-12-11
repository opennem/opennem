from typing import List

from opennem.api.export.map import PriorityType, StatExport, StatType
from opennem.api.export.tasks import export_energy, export_power
from opennem.api.stats.controllers import get_scada_range
from opennem.api.time import human_to_period
from opennem.core.network_region_bom_station_map import (
    get_network_region_weather_station,
)
from opennem.core.networks import network_from_network_code
from opennem.schema.network import NetworkAPVI, NetworkWEM


def run_tests() -> None:
    network_schema = network_from_network_code("WEM")
    scada_range = get_scada_range(network=network_schema)
    bom_station = get_network_region_weather_station("WEM")

    export = StatExport(
        stat_type=StatType.power,
        priority=PriorityType.live,
        country="au",
        date_range=scada_range,
        network=network_schema,
        networks=[NetworkAPVI, NetworkWEM],
        bom_station=bom_station,
        network_region_query="WEM",
        period=human_to_period("7d"),
    )

    export_power(stats=[export])

    # export = StatExport(
    #     stat_type=StatType.power,
    #     priority=PriorityType.live,
    #     country="au",
    #     date_range=scada_range,
    #     network=network_schema,
    #     network_region="NSW1",
    #     bom_station=bom_station,
    #     period=human_to_period("7d"),
    # )

    # export_power(stats=[export])

    # export = StatExport(
    #     stat_type=StatType.energy,
    #     priority=PriorityType.monthly,
    #     country="au",
    #     date_range=scada_range,
    #     network=network_schema,
    #     network_region=None,
    #     bom_station=bom_station,
    #     period=human_to_period("all"),
    # )

    # export_energy(stats=[export])

    # power_stats = export_map.resources


if __name__ == "__main__":
    run_tests()
