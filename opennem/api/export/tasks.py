"""
Tasks file to expor JSON's to S3 or locally for the
opennem website

This is the most frequently accessed content that doesn't
require the API


"""

import logging
from datetime import datetime
from typing import List, Optional

from opennem.api.export.controllers import (
    energy_fueltech_daily,
    energy_interconnector_region_daily,
    gov_stats_cpi,
    power_flows_week,
    power_week,
    weather_daily,
)
from opennem.api.export.map import PriorityType, StatExport, StatType, get_export_map
from opennem.api.export.utils import write_output
from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import OpennemDataSet
from opennem.core.network_region_bom_station_map import get_network_region_weather_station
from opennem.core.networks import network_from_network_code
from opennem.db import SessionLocal
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.network import NetworkAPVI, NetworkNEM, NetworkWEM
from opennem.settings import settings
from opennem.utils.version import get_version

logger = logging.getLogger(__name__)


def export_power(
    stats: List[StatExport] = None,
    priority: Optional[PriorityType] = None,
    latest: Optional[bool] = False,
) -> None:
    """
    Export power stats from the export map


    """
    if not stats:
        export_map = get_export_map()
        stats = export_map.get_by_stat_type(StatType.power, priority)

    output_count: int = 0

    for power_stat in stats:
        if power_stat.stat_type != StatType.power:
            continue

        if output_count >= 1 and latest:
            return None

        stat_set = power_week(
            date_range=power_stat.date_range,
            period=power_stat.period,
            network_code=power_stat.network.code,
            network_region_code=power_stat.network_region_query or power_stat.network_region,
            networks_query=power_stat.networks,
        )

        if not stat_set:
            logger.info(
                "No power stat set for {} {} {}".format(
                    power_stat.period,
                    power_stat.networks,
                    power_stat.network_region,
                )
            )
            continue

        if power_stat.network_region:
            flow_set = power_flows_week(
                network=NetworkNEM,
                date_range=power_stat.date_range,
                network_region_code=power_stat.network_region,
            )

            if flow_set:
                stat_set.append_set(flow_set)

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
        output_count += 1


def export_energy(
    stats: List[StatExport] = None,
    priority: Optional[PriorityType] = None,
    latest: Optional[bool] = False,
) -> None:
    """
    Export energy stats from the export map


    """
    if not stats:
        export_map = get_export_map()
        stats = export_map.get_by_stat_type(StatType.energy, priority)

    CURRENT_YEAR = datetime.now().year

    for energy_stat in stats:
        if energy_stat.stat_type != StatType.energy:
            continue

        # @FIX trim to NEM since it's the one with the shortest
        # data time span.
        # @TODO find a better and more flexible way to do this in the
        # range method
        date_range_networks = energy_stat.networks or []

        if NetworkNEM in date_range_networks:
            date_range_networks = [NetworkNEM]

        date_range = get_scada_range(network=energy_stat.network, networks=date_range_networks)

        if energy_stat.year:

            if latest and energy_stat.year != CURRENT_YEAR:
                continue

            stat_set = energy_fueltech_daily(
                interval_size="1d",
                year=energy_stat.year,
                network=energy_stat.network,
                networks_query=energy_stat.networks,
                date_range=date_range,
                network_region_code=energy_stat.network_region_query or energy_stat.network_region,
            )

            if not stat_set:
                continue

            # Hard coded to NEM only atm but we'll put has_interconnectors
            # in the metadata to automate all this
            if energy_stat.network == NetworkNEM and energy_stat.network_region:
                interconnector_flows = energy_interconnector_region_daily(
                    interval_size="1d",
                    year=energy_stat.year,
                    network=energy_stat.network,
                    networks_query=energy_stat.networks,
                    date_range=date_range,
                    network_region_code=energy_stat.network_region_query
                    or energy_stat.network_region,
                )
                stat_set.append_set(interconnector_flows)

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
                date_range=date_range,
                network_region_code=energy_stat.network_region_query or energy_stat.network_region,
            )

            if not stat_set:
                continue

            # Hard coded to NEM only atm but we'll put has_interconnectors
            # in the metadata to automate all this
            if energy_stat.network == NetworkNEM and energy_stat.network_region:
                interconnector_flows = energy_interconnector_region_daily(
                    interval_size="1M",
                    network=energy_stat.network,
                    networks_query=energy_stat.networks,
                    date_range=date_range,
                    network_region_code=energy_stat.network_region_query
                    or energy_stat.network_region,
                )
                stat_set.append_set(interconnector_flows)

            if energy_stat.bom_station:
                weather_stats = weather_daily(
                    station_code=energy_stat.bom_station,
                    date_range=date_range,
                    year=energy_stat.year,
                    network_code=energy_stat.network.code,
                )
                stat_set.append_set(weather_stats)

            write_output(energy_stat.path, stat_set)


def export_all_monthly() -> None:
    session = SessionLocal()
    network_regions = session.query(NetworkRegion).all()

    all_monthly = OpennemDataSet(
        code="au", data=[], version=get_version(), created_at=datetime.now()
    )

    cpi = gov_stats_cpi()
    all_monthly.append_set(cpi)

    for network_region in network_regions:
        network = network_from_network_code(network_region.network.code)
        networks = None

        if network_region.code == "WEM":
            networks = [NetworkWEM, NetworkAPVI]

        stat_set = energy_fueltech_daily(
            interval_size="1M",
            network=network,
            networks_query=networks,
            network_region_code=network_region.code,
        )

        if not stat_set:
            continue

        if network == NetworkNEM:
            interconnector_flows = energy_interconnector_region_daily(
                interval_size="1M",
                network=network,
                networks_query=networks,
                network_region_code=network_region.code,
            )
            stat_set.append_set(interconnector_flows)

        all_monthly.append_set(stat_set)

        bom_station = get_network_region_weather_station(network_region.code)

        if bom_station:
            weather_stats = weather_daily(
                station_code=bom_station,
                network_code=network.code,
            )
            all_monthly.append_set(weather_stats)

    write_output("v3/stats/au/all/monthly.json", all_monthly)


def export_all_daily() -> None:
    session = SessionLocal()
    network_regions = session.query(NetworkRegion).all()

    cpi = gov_stats_cpi()

    for network_region in network_regions:
        network = network_from_network_code(network_region.network.code)
        networks = None

        if network_region.code == "WEM":
            networks = [NetworkWEM, NetworkAPVI]

        stat_set = energy_fueltech_daily(
            interval_size="1d",
            network=network,
            networks_query=networks,
            network_region_code=network_region.code,
        )

        if not stat_set:
            continue

        # Hard coded to NEM only atm but we'll put has_interconnectors
        # in the metadata to automate all this
        if network == NetworkNEM:
            interconnector_flows = energy_interconnector_region_daily(
                interval_size="1d",
                network=network,
                networks_query=networks,
                network_region_code=network_region.code,
            )
            stat_set.append_set(interconnector_flows)

        bom_station = get_network_region_weather_station(network_region.code)

        if bom_station:
            weather_stats = weather_daily(
                station_code=bom_station,
                network_code=network.code,
            )
            stat_set.append_set(weather_stats)

        if cpi:
            stat_set.append_set(cpi)

        write_output(f"v3/stats/au/{network_region.code}/daily.json", stat_set)


def export_metadata() -> bool:
    """
    Export metadata


    """
    _export_map_out = get_export_map()

    # this is a hack because pydantic doesn't
    # serialize properties
    for r in _export_map_out.resources:
        r.file_path = r.path

    wrote_bytes = write_output("metadata.json", _export_map_out)

    if wrote_bytes and wrote_bytes > 0:
        return True

    return False


if __name__ == "__main__":
    export_all_daily()
    # export_all_monthly()
    # export_energy()
    # export_all_daily()

    # export_power(priority=PriorityType.history)

    # if settings.env in ["development", "staging"]:
    #     export_power(priority=PriorityType.live)
    #     export_energy(latest=True)
    #     export_metadata()
    #     # export_power(priority=PriorityType.history)
    # else:
    #     # export_power(priority=PriorityType.live)
    #     # export_energy(latest=True)
    #     export_energy()
    #     # export_metadata()
    #     # export_power(priority=PriorityType.history)
