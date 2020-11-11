import logging
from datetime import datetime
from typing import List, Optional

from opennem.api.export.controllers import (
    energy_fueltech_daily,
    power_week,
    weather_daily,
)
from opennem.api.export.map import (
    PriorityType,
    StatExport,
    StatType,
    get_export_map,
)
from opennem.api.export.utils import write_output
from opennem.api.stats.router import price_network_region_api
from opennem.db import get_database_engine
from opennem.schema.network import NetworkWEM
from opennem.settings import settings

# @TODO q this ..
# @NOTE done in new stat export maps
YEAR_MIN = 2010

logger = logging.getLogger(__name__)

export_map = get_export_map()


def export_power(priority: Optional[PriorityType] = None):
    power_stat_sets = export_map.get_by_stat_type(StatType.power, priority)

    for power_stat in power_stat_sets:
        stat_set = power_week(
            network_code=power_stat.network.code,
            network_region_code=power_stat.network_region,
            networks=power_stat.networks,
        )

        if power_stat.bom_station:
            weather_set = weather_daily(
                station_code=power_stat.bom_station,
                network_code=power_stat.network.code,
                include_min_max=False,
                period_human="7d",
                unit_name="temperature",
            )

            stat_set.append_set(weather_set)

        write_output(power_stat.path, stat_set)


def export_energy(
    priority: Optional[PriorityType] = None, latest: bool = False
):
    energy_stat_sets = export_map.get_by_stat_type(StatType.energy, priority)

    CURRENT_YEAR = datetime.now().year

    for energy_stat in energy_stat_sets:
        if energy_stat.year:

            if latest and energy_stat.year != CURRENT_YEAR:
                continue

            stat_set = energy_fueltech_daily(
                year=energy_stat.year,
                network=energy_stat.network,
                networks=energy_stat.networks,
                network_region_code=energy_stat.network_region,
            )

            if energy_stat.bom_station:
                weather_stats = weather_daily(
                    station_code=energy_stat.bom_station,
                    year=energy_stat.year,
                    network_code=energy_stat.network.code,
                )
                stat_set.append_set(weather_stats)

            write_output(energy_stat.path, stat_set)

        elif energy_stat.period.period_human == "all":
            stat_set = energy_fueltech_daily(
                interval_size="1M",
                network=energy_stat.network,
                networks=energy_stat.networks,
                network_region_code=energy_stat.network_region,
            )

            if energy_stat.bom_station:
                weather_stats = weather_daily(
                    station_code=energy_stat.bom_station,
                    year=energy_stat.year,
                    network_code=energy_stat.network.code,
                )
                stat_set.append_set(weather_stats)

            write_output(energy_stat.path, stat_set)


def export_metadata():

    _export_map_out = export_map

    # this is a hack because pydantic doesn't
    # serialize properties
    for r in _export_map_out.resources:
        r.file_path = r.path()

    write_output("metadata.json", _export_map_out)


def wem_export_power(is_local: bool = False):
    engine = get_database_engine()

    stat_set = power_week(network_code="WEM")

    stat_set.data += weather_daily(
        station_code="009021",
        network_code="WEM",
        include_min_max=False,
        period_human="7d",
        unit_name="temperature",
    ).data

    price = price_network_region_api(
        engine=engine,
        network_code="WEM",
        network_region_code="WEM",
        interval="30m",
        period="7d",
    )

    stat_set.data = stat_set.data + price.data

    POWER_ENDPOINT = "/power/wem.json"

    write_output(POWER_ENDPOINT, stat_set, is_local=is_local)


def wem_export_daily(limit: int = None, is_local: bool = False):
    processed_years = 0

    for year in range(datetime.now().year, YEAR_MIN - 1, -1):

        stat_set = energy_fueltech_daily(year=year, network=NetworkWEM)

        weather = weather_daily(
            station_code="009021", year=year, network_code="WEM",
        )
        stat_set.data += weather.data

        write_output(
            f"/wem/energy/daily/{year}.json", stat_set, is_local=is_local
        )

        processed_years += 1

        if limit and limit >= processed_years:
            return None


def wem_export_monthly(is_local: bool = False):
    """

    """

    stat_set = energy_fueltech_daily(network=NetworkWEM, interval_size="1M")

    stat_set.data += weather_daily(
        station_code="009021", network_code="WEM",
    ).data

    write_output(
        "/wem/energy/monthly/all.json", stat_set, is_local=is_local,
    )


if __name__ == "__main__":
    if settings.env in ["development", "staging"]:
        export_power(priority=PriorityType.live)
        export_energy(latest=True)
        # export_metadata()
        # wem_export_power(is_local=True)
        # wem_export_daily(limit=1, is_local=True)
        # wem_export_monthly(is_local=True)
    else:
        wem_export_power()
        wem_export_daily()
        wem_export_monthly()
