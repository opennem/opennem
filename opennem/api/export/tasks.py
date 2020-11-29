import logging
from datetime import datetime
from typing import Optional

from opennem.api.export.controllers import (
    energy_fueltech_daily,
    power_week,
    weather_daily,
)
from opennem.api.export.map import PriorityType, StatType, get_export_map
from opennem.api.export.utils import write_output
from opennem.settings import settings

logger = logging.getLogger(__name__)

export_map = get_export_map()


def export_power(
    priority: Optional[PriorityType] = None, latest: bool = False
) -> None:
    power_stat_sets = export_map.get_by_stat_type(StatType.power, priority)

    output_count: int = 0

    for power_stat in power_stat_sets:

        if output_count >= 1 and latest:
            return None

        stat_set = power_week(
            date_range=power_stat.date_range,
            period=power_stat.period,
            network_code=power_stat.network.code,
            network_region_code=power_stat.network_region,
            networks_query=power_stat.networks,
        )

        if not stat_set:
            continue

        if power_stat.bom_station:
            weather_set = weather_daily(
                station_code=power_stat.bom_station,
                network_code=power_stat.network.code,
                include_min_max=False,
                period_human="7d",
                unit_name="temperature",
            )

            stat_set.append_set(weather_set)

        # print(power_stat.path)
        write_output(power_stat.path, stat_set)
        output_count += 1


def export_energy(
    priority: Optional[PriorityType] = None, latest: bool = False
) -> None:
    energy_stat_sets = export_map.get_by_stat_type(StatType.energy, priority)

    CURRENT_YEAR = datetime.now().year

    for energy_stat in energy_stat_sets:
        if energy_stat.year:

            if latest and energy_stat.year != CURRENT_YEAR:
                continue

            stat_set = energy_fueltech_daily(
                year=energy_stat.year,
                network=energy_stat.network,
                networks_query=energy_stat.networks,
                network_region_code=energy_stat.network_region,
            )

            if not stat_set:
                continue

            if energy_stat.bom_station:
                weather_stats = weather_daily(
                    station_code=energy_stat.bom_station,
                    year=energy_stat.year,
                    network_code=energy_stat.network.code,
                )
                stat_set.append_set(weather_stats)

            write_output(energy_stat.path, stat_set)

        elif energy_stat.period and energy_stat.period.period_human == "all":
            stat_set = energy_fueltech_daily(
                interval_size="1M",
                network=energy_stat.network,
                networks_query=energy_stat.networks,
                network_region_code=energy_stat.network_region,
            )

            if not stat_set:
                continue

            if energy_stat.bom_station:
                weather_stats = weather_daily(
                    station_code=energy_stat.bom_station,
                    year=energy_stat.year,
                    network_code=energy_stat.network.code,
                )
                stat_set.append_set(weather_stats)

            write_output(energy_stat.path, stat_set)


def export_metadata() -> None:

    _export_map_out = export_map

    # this is a hack because pydantic doesn't
    # serialize properties
    for r in _export_map_out.resources:
        r.file_path = r.path

    write_output("metadata.json", _export_map_out)


if __name__ == "__main__":
    if settings.env in ["development", "staging"]:
        export_power(priority=PriorityType.live)
        export_energy(latest=True)
        export_power(priority=PriorityType.history)
        export_metadata()
    else:
        export_power()
        export_power(priority=PriorityType.history)
        export_energy()
        export_metadata()
