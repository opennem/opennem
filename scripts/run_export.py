#!/usr/bin/env python
from typing import List

from opennem.api.export.controllers import (
    energy_fueltech_daily,
    energy_interconnector_emissions_region_daily,
    energy_interconnector_region_daily,
)
from opennem.api.export.map import PriorityType, StatExport, StatType, get_export_map
from opennem.api.export.tasks import export_energy, export_power
from opennem.api.export.utils import write_output
from opennem.api.stats.controllers import get_scada_range
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.network_region_bom_station_map import get_network_region_weather_station
from opennem.core.networks import network_from_network_code
from opennem.schema.network import NetworkAPVI, NetworkAU, NetworkNEM, NetworkWEM


def run_tests() -> None:
    network_schema = network_from_network_code("NEM")
    scada_range = get_scada_range(network=network_schema)
    bom_station = get_network_region_weather_station("NEM")

    # interconnector_flows = energy_interconnector_emissions_region_daily(
    #     interval_size="1d",
    #     year=2021,
    #     network=NetworkNEM,
    #     # networks_query=energy_stat.networks,
    #     date_range=scada_range,
    #     network_region_code="TAS1",
    # )

    # with open("tas1.json", "w") as fh:
    #     fh.write(interconnector_flows.json(indent=4))

    # return None

    # export_map = get_export_map()

    # def get_wem(i):
    #     if (
    #         i.stat_type == StatType.energy
    #         and i.priority == PriorityType.monthly
    #         and i.network == NetworkWEM
    #     ):
    #         return i

    # wem_all = list(filter(lambda i: get_wem(i), export_map.resources))

    # for w in wem_all:
    #     print(w.path)

    # export = StatExport(
    #     stat_type=StatType.power,
    #     priority=PriorityType.live,
    #     country="au",
    #     date_range=scada_range,
    #     network_region="TAS1",
    #     network=NetworkNEM,
    #     # networks=[NetworkNEM, NetworkWEM],
    #     period=human_to_period("7d"),
    # )

    # export_power(stats=[export])

    # network = network_from_network_code("NEM")
    # networks = None

    # stat_set = energy_fueltech_daily(
    #     interval_size="1d",
    #     network=network,
    #     networks_query=networks,
    #     network_region_code="SA1",
    # )

    # write_output(f"v3/stats/au/SA1/daily.json", stat_set)

    # export_energy(stats=wem_all)
    # export = StatExport(
    #     stat_type=StatType.power,
    #     priority=PriorityType.live,
    #     country="au",
    #     date_range=scada_range,
    #     network=network_schema,
    #     networks=[NetworkAPVI, NetworkWEM],
    #     bom_station=bom_station,
    #     network_region_query="WEM",
    #     period=human_to_period("7d"),
    # )

    # export_power(stats=[export])

    # export = StatExport(
    #     stat_type=StatType.power,
    #     priority=PriorityType.live,
    #     country="au",
    #     date_range=scada_range,
    #     network=network_schema,
    #     network_region="NSW1",
    #     bom_station=get_network_region_weather_station("NSW1"),
    #     period=human_to_period("7d"),
    # )

    # export_power(stats=[export])

    # export = StatExport(
    #     stat_type=StatType.energy,
    #     priority=PriorityType.monthly,
    #     country="au",
    #     date_range=scada_range,
    #     network=network_schema,
    #     network_region="TAS1",
    #     bom_station=get_network_region_weather_station("TAS1"),
    #     year=2020,
    # )

    # export_energy(stats=[export])

    # return None

    # for region in ["TAS1", "NSW1"]:
    for region in ["SA1"]:
        export = StatExport(
            stat_type=StatType.power,
            priority=PriorityType.live,
            country="au",
            date_range=scada_range,
            network_region=region,
            network=NetworkNEM,
            bom_station=get_network_region_weather_station(region),
            # networks=[NetworkNEM, NetworkWEM],
            period=human_to_period("7d"),
            interval=NetworkNEM.get_interval(),
        )

        # export_power(stats=[export])

        for y in [2021]:
            export = StatExport(
                stat_type=StatType.energy,
                priority=PriorityType.monthly,
                country="au",
                date_range=scada_range,
                network=network_schema,
                network_region=region,
                bom_station=get_network_region_weather_station(region),
                year=y,
                interval=human_to_interval("1d"),
            )

            export_energy(stats=[export])

        # export = StatExport(
        #     stat_type=StatType.energy,
        #     priority=PriorityType.monthly,
        #     country="au",
        #     date_range=scada_range,
        #     network=network_schema,
        #     network_region=region,
        #     bom_station=get_network_region_weather_station(region),
        #     period=human_to_period("all"),
        #     interval=human_to_interval("1M"),
        # )

        # export_energy(stats=[export])

    # power_stats = export_map.resources

    # export = StatExport(
    #     stat_type=StatType.energy,
    #     priority=PriorityType.monthly,
    #     country="au",
    #     date_range=scada_range,
    #     network=network_schema,
    #     bom_station=bom_station,
    #     period=human_to_period("all"),
    # )

    # export_energy(stats=[export])


if __name__ == "__main__":
    run_tests()
