"""
Tasks file to expor JSON's to S3 or locally for the
opennem website

This is the most frequently accessed content that doesn't
require the API


"""


import contextlib
import logging
from datetime import datetime
from typing import List, Optional

from datetime_truncate import truncate as date_trunc

from opennem.api.export.controllers import (
    NoResults,
    demand_network_region_daily,
    demand_week,
    energy_fueltech_daily,
    energy_interconnector_flows_and_emissions,
    gov_stats_cpi,
    power_flows_network_week,
    power_flows_region_week,
    power_week,
    weather_daily,
)
from opennem.api.export.map import PriorityType, StatExport, StatType, get_export_map, get_weekly_export_map
from opennem.api.export.utils import write_output
from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import OpennemDataSet, ScadaDateRange
from opennem.api.time import human_to_interval, human_to_period
from opennem.controllers.output.flows import (
    energy_interconnector_emissions_region_daily,
    energy_interconnector_region_daily,
)
from opennem.core.flows import invert_flow_set
from opennem.core.network_region_bom_station_map import get_network_region_weather_station
from opennem.core.network_regions import get_network_regions
from opennem.core.time import get_interval
from opennem.db import get_scoped_session
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.dates import DatetimeRange, TimeSeries
from opennem.schema.network import (
    NetworkAEMORooftop,
    NetworkAEMORooftopBackfill,
    NetworkAPVI,
    NetworkNEM,
    NetworkSchema,
    NetworkWEM,
)
from opennem.settings import settings
from opennem.utils.version import get_version

logger = logging.getLogger("opennem.export.tasks")


def export_power(
    stats: List[StatExport] = None,
    priority: Optional[PriorityType] = None,
    latest: Optional[bool] = False,
) -> None:
    """
    Export power stats from the export map


    """

    # Not passed a stat map so go and get one
    if not stats:
        export_map = None

        if priority and priority == PriorityType.history:
            export_map = get_weekly_export_map()

        else:
            export_map = get_export_map().get_by_stat_type(StatType.power)

        if priority:
            export_map = export_map.get_by_priority(priority)

        stats = export_map.resources

    output_count: int = 0

    logger.info(f"Running export_power {latest=} {priority} with {len(stats)} stats")

    for power_stat in stats:
        if power_stat.stat_type != StatType.power:
            continue

        if output_count >= 1 and latest:
            return None

        date_range_networks = power_stat.networks or []

        if NetworkNEM in date_range_networks:
            date_range_networks = [NetworkNEM]

        date_range: ScadaDateRange = get_scada_range(network=power_stat.network, networks=date_range_networks)

        logger.debug(f"Date range for {power_stat.network.code}: {date_range.start} => {date_range.end}")

        # Migrate to this time_series
        time_series = TimeSeries(
            start=date_range.start,
            end=date_range.end,
            network=power_stat.network,
            year=power_stat.year,
            interval=power_stat.interval,
            period=power_stat.period,
        )

        stat_set = power_week(
            time_series=time_series,
            network_region_code=power_stat.network_region_query or power_stat.network_region,
            networks_query=power_stat.networks,
        )

        if not stat_set:
            logger.info(f"No power stat set for {power_stat.period} {power_stat.networks} {power_stat.network_region}")

            continue

        demand_set = demand_week(
            time_series=time_series,
            networks_query=power_stat.networks,
            network_region_code=power_stat.network_region_query or power_stat.network_region,
        )

        stat_set.append_set(demand_set)

        if power_stat.network_region:
            if flow_set := power_flows_region_week(
                time_series=time_series,
                network_region_code=power_stat.network_region,
            ):
                stat_set.append_set(flow_set)

        time_series_weather = time_series.copy()
        time_series_weather.interval = human_to_interval("30m")

        if power_stat.bom_station:
            with contextlib.suppress(Exception):
                weather_set = weather_daily(
                    time_series=time_series_weather,
                    station_code=power_stat.bom_station,
                    network_region=power_stat.network_region,
                    include_min_max=False,
                    unit_name="temperature",
                    network=power_stat.network,
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
        export_map = get_export_map().get_by_stat_type(StatType.energy)

        if priority:
            export_map = export_map.get_by_priority(priority)

        stats = export_map.resources

    CURRENT_YEAR = datetime.now().year

    logger.info(f"Running export_energy with {len(stats)} stats")

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

        date_range: ScadaDateRange = get_scada_range(
            network=energy_stat.network, networks=date_range_networks, energy=True
        )

        if not date_range:
            logger.error(
                "Skipping - Could not get date range for energy {} {}".format(energy_stat.network, date_range_networks)
            )
            continue

        logger.debug("Date range is: {} {} => {}".format(energy_stat.network.code, date_range.start, date_range.end))

        # Migrate to this time_series
        time_series = TimeSeries(
            start=date_range.start,
            end=date_range.end,
            network=energy_stat.network,
            year=energy_stat.year,
            interval=energy_stat.interval,
            period=human_to_period("1Y"),
            # v4 fields
            time_range=DatetimeRange(start=date_range.start, end=date_range.end, interval=get_interval("1Y")),
        )

        if energy_stat.year:

            if latest and energy_stat.year != CURRENT_YEAR:
                continue

            stat_set = energy_fueltech_daily(
                time_series=time_series,
                networks_query=energy_stat.networks,
                network_region_code=energy_stat.network_region_query or energy_stat.network_region,
            )

            if not stat_set:
                continue

            demand_energy_and_value = demand_network_region_daily(
                time_series=time_series, network_region_code=energy_stat.network_region, networks=energy_stat.networks
            )
            stat_set.append_set(demand_energy_and_value)

            # Hard coded to NEM only atm but we'll put has_interconnectors
            # in the metadata to automate all this
            if energy_stat.network.has_interconnectors and energy_stat.network_region:
                if settings.flows_and_emissions_v2:
                    interconnector_flows = energy_interconnector_flows_and_emissions(
                        time_series=time_series,
                        networks_query=energy_stat.networks,
                        network_region_code=energy_stat.network_region_query or energy_stat.network_region,
                    )
                    stat_set.append_set(interconnector_flows)
                else:
                    interconnector_flows = energy_interconnector_region_daily(
                        time_series=time_series,
                        # networks_query=energy_stat.networks,
                        network_region_code=energy_stat.network_region_query or energy_stat.network_region,
                    )
                    stat_set.append_set(interconnector_flows)

                    interconnector_emissions = energy_interconnector_emissions_region_daily(
                        time_series=time_series,
                        networks_query=energy_stat.networks,
                        network_region_code=energy_stat.network_region_query or energy_stat.network_region,
                    )
                    stat_set.append_set(interconnector_emissions)

            if energy_stat.bom_station:
                try:
                    weather_stats = weather_daily(
                        time_series=time_series,
                        station_code=energy_stat.bom_station,
                        network_region=energy_stat.network_region,
                    )
                    stat_set.append_set(weather_stats)
                except NoResults as e:
                    logger.info("No results for weather result: {}".format(e))
                except Exception as e:
                    logger.error("weather_stat exception: {}".format(e))
                    pass
            else:
                logger.info("Stat set has no bom station")

            write_output(energy_stat.path, stat_set)

        elif energy_stat.period and energy_stat.period.period_human == "all" and not latest:
            time_series.period = human_to_period("all")
            time_series.interval = human_to_interval("1M")
            time_series.year = None

            stat_set = energy_fueltech_daily(
                time_series=time_series,
                networks_query=energy_stat.networks,
                network_region_code=energy_stat.network_region_query or energy_stat.network_region,
            )

            if not stat_set:
                continue

            demand_energy_and_value = demand_network_region_daily(
                time_series=time_series, network_region_code=energy_stat.network_region, networks=energy_stat.networks
            )
            stat_set.append_set(demand_energy_and_value)

            # Hard coded to NEM only atm but we'll put has_interconnectors
            # in the metadata to automate all this
            if energy_stat.network == NetworkNEM and energy_stat.network_region:
                if settings.flows_and_emissions_v2:
                    interconnector_flows = energy_interconnector_flows_and_emissions(
                        time_series=time_series,
                        networks_query=energy_stat.networks,
                        network_region_code=energy_stat.network_region_query or energy_stat.network_region,
                    )
                    stat_set.append_set(interconnector_flows)
                else:
                    interconnector_flows = energy_interconnector_region_daily(
                        time_series=time_series,
                        # networks_query=energy_stat.networks,
                        network_region_code=energy_stat.network_region_query or energy_stat.network_region,
                    )
                    stat_set.append_set(interconnector_flows)

                    interconnector_emissions = energy_interconnector_emissions_region_daily(
                        time_series=time_series,
                        networks_query=energy_stat.networks,
                        network_region_code=energy_stat.network_region_query or energy_stat.network_region,
                    )
                    stat_set.append_set(interconnector_emissions)

            if energy_stat.bom_station:
                try:
                    weather_stats = weather_daily(
                        time_series=time_series,
                        station_code=energy_stat.bom_station,
                        network_region=energy_stat.network_region,
                    )
                    stat_set.append_set(weather_stats)
                except NoResults as e:
                    logger.info("No weather results: {}".format(e))
                except Exception:
                    pass

            write_output(energy_stat.path, stat_set)


def export_all_monthly() -> None:
    session = get_scoped_session()

    all_monthly = OpennemDataSet(code="au", data=[], version=get_version(), created_at=datetime.now())

    cpi = gov_stats_cpi()
    all_monthly.append_set(cpi)

    # Iterate networks and network regions
    networks = [NetworkNEM, NetworkWEM]

    for network in networks:
        network_regions = session.query(NetworkRegion).filter(NetworkRegion.network_id == network.code).all()

        for network_region in network_regions:
            networks = []

            logging.info(f"Exporting monthly for network {network.code} and region {network_region.code}")

            if network_region.code == "WEM":
                networks = [NetworkWEM, NetworkAPVI]

            if network == NetworkNEM:
                networks = [NetworkNEM, NetworkAEMORooftop]

            logger.debug(f"Running monthlies for {network.code} and {network_region.code}")

            scada_range: ScadaDateRange = get_scada_range(network=network, networks=networks, energy=True)

            if not scada_range or not scada_range.start:
                logger.error(f"Could not get scada range for network {network} and energy True")

                continue

            time_series = TimeSeries(
                start=scada_range.start,
                end=scada_range.end,
                network=network,
                interval=get_interval("1M"),
                period=human_to_period("all"),
                time_range=DatetimeRange(
                    start=date_trunc(scada_range.start, "month"),
                    end=date_trunc(scada_range.end, "month"),
                    interval=get_interval("1M"),
                ),
            )

            stat_set = energy_fueltech_daily(
                time_series=time_series,
                networks_query=networks,
                network_region_code=network_region.code,
            )

            if not stat_set:
                continue

            demand_energy_and_value = demand_network_region_daily(
                time_series=time_series, network_region_code=network_region.code, networks=networks
            )
            stat_set.append_set(demand_energy_and_value)

            if network.has_interconnectors:

                if settings.flows_and_emissions_v2:
                    interconnector_flows = energy_interconnector_flows_and_emissions(
                        time_series=time_series,
                        networks_query=networks,
                        network_region_code=network_region.code,
                    )
                    stat_set.append_set(interconnector_flows)
                else:
                    interconnector_flows = energy_interconnector_region_daily(
                        time_series=time_series,
                        # networks_query=energy_stat.networks,
                        network_region_code=network_region.code,
                    )
                    stat_set.append_set(interconnector_flows)

                    interconnector_emissions = energy_interconnector_emissions_region_daily(
                        time_series=time_series,
                        networks_query=networks,
                        network_region_code=network_region.code,
                    )
                    stat_set.append_set(interconnector_emissions)

            all_monthly.append_set(stat_set)

            if bom_station := get_network_region_weather_station(network_region.code):
                with contextlib.suppress(Exception):
                    weather_stats = weather_daily(
                        time_series=time_series,
                        station_code=bom_station,
                        network_region=network_region.code,
                        network=network,
                    )
                    all_monthly.append_set(weather_stats)

    write_output("v3/stats/au/all/monthly.json", all_monthly)


def export_all_daily(networks: List[NetworkSchema] = None, network_region_code: Optional[str] = None) -> None:
    """Export dailies for all networks and regions"""

    # default list of networks
    if networks is None:
        networks = [NetworkNEM, NetworkWEM]

    session = get_scoped_session()

    cpi = gov_stats_cpi()

    for network in networks:
        network_regions = session.query(NetworkRegion).filter_by(export_set=True).filter_by(network_id=network.code)

        if network_region_code:
            network_regions = network_regions.filter_by(code=network_region_code)

        network_regions = network_regions.all()

        for network_region in network_regions:

            logging.info(f"Exporting for network {network.code} and region {network_region.code}")

            networks = [NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill]

            if network_region.code == "WEM":
                networks = [NetworkWEM, NetworkAPVI]

            scada_range: ScadaDateRange = get_scada_range(network=network, networks=networks, energy=True)

            if not scada_range or not scada_range.start:
                logger.error(f"Could not get scada range for network {network} and energy True")

                continue

            time_series = TimeSeries(
                start=scada_range.start,
                end=scada_range.end,
                network=network,
                interval=human_to_interval("1d"),
                period=human_to_period("all"),
                time_range=DatetimeRange(
                    start=date_trunc(scada_range.start, "day"),
                    end=date_trunc(scada_range.end, "day"),
                    interval=get_interval("1d"),
                ),
            )

            stat_set = energy_fueltech_daily(
                time_series=time_series,
                networks_query=networks,
                network_region_code=network_region.code,
            )

            if not stat_set:
                continue

            demand_energy_and_value = demand_network_region_daily(
                time_series=time_series, network_region_code=network_region.code, networks=networks
            )
            stat_set.append_set(demand_energy_and_value)

            # Hard coded to NEM only atm but we'll put has_interconnectors
            # in the metadata to automate all this
            if network == NetworkNEM:
                interconnector_flows = energy_interconnector_flows_and_emissions(
                    time_series=time_series,
                    networks_query=networks,
                    network_region_code=network_region.code,
                )
                stat_set.append_set(interconnector_flows)

            if bom_station := get_network_region_weather_station(network_region.code):
                with contextlib.suppress(Exception):
                    weather_stats = weather_daily(
                        time_series=time_series,
                        station_code=bom_station,
                        network_region=network_region.code,
                    )
                    stat_set.append_set(weather_stats)
            if cpi:
                stat_set.append_set(cpi)

            write_output(f"v3/stats/au/{network_region.code}/daily.json", stat_set)


def export_flows() -> None:
    date_range = get_scada_range(network=NetworkNEM)

    interchange_stat = StatExport(
        stat_type=StatType.power,
        priority=PriorityType.live,
        country="au",
        date_range=date_range,
        network=NetworkNEM,
        interval=NetworkNEM.get_interval(),
        period=human_to_period("7d"),
    )

    time_series = TimeSeries(
        start=date_range.start,
        end=date_range.end,
        network=interchange_stat.network,
        interval=interchange_stat.interval,
        period=interchange_stat.period,
    )

    stat_set = power_flows_network_week(time_series=time_series)

    if stat_set:
        write_output(f"v3/stats/au/{interchange_stat.network.code}/flows/7d.json", stat_set)


def export_electricitymap() -> None:
    date_range = get_scada_range(network=NetworkNEM)

    if not date_range or date_range.start:
        raise Exception("Could not get a scada range in EM export")

    interchange_stat = StatExport(
        stat_type=StatType.power,
        priority=PriorityType.live,
        country="au",
        date_range=date_range,
        network=NetworkNEM,
        interval=NetworkNEM.get_interval(),
        period=human_to_period("1d"),
    )

    time_series = TimeSeries(
        start=date_range.start,
        end=date_range.end,
        network=interchange_stat.network,
        networks=[NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill],
        interval=interchange_stat.interval,
        period=interchange_stat.period,
    )

    stat_set = power_flows_network_week(time_series=time_series)

    if not stat_set:
        logger.warning("No flow results for electricitymap export")
        return None

    em_set = OpennemDataSet(type="custom", version=get_version(), created_at=datetime.now(), data=[])

    INVERT_SETS = ["VIC1->NSW1", "VIC1->SA1"]

    for ds in stat_set.data:
        if ds.code in INVERT_SETS:
            ds_inverted = invert_flow_set(ds)
            em_set.data.append(ds_inverted)
            logging.info("Inverted {}".format(ds.code))
        else:
            em_set.data.append(ds)

    for region in ["NSW1", "QLD1", "VIC1", "TAS1", "SA1"]:
        power_set = power_week(
            time_series,
            region,
            include_capacities=True,
            networks_query=[NetworkNEM, NetworkAEMORooftop, NetworkAEMORooftopBackfill],
        )

        if power_set:
            em_set.append_set(power_set)

    date_range = get_scada_range(network=NetworkWEM)

    # WEM custom
    time_series = TimeSeries(
        start=date_range.start,
        end=date_range.end,
        network=NetworkWEM,
        networks=[NetworkWEM, NetworkAPVI],
        interval=NetworkWEM.get_interval(),
        period=interchange_stat.period,
    )

    power_set = power_week(
        time_series,
        "WEM",
        include_capacities=True,
        networks_query=[NetworkWEM, NetworkAPVI],
    )

    if power_set:
        em_set.append_set(power_set)

    write_output("v3/clients/em/latest.json", em_set)


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


# Debug Hooks
if __name__ == "__main__":
    # export_power(priority=PriorityType.live)
    export_energy(latest=True)
    # export_all_monthly()
    # export_all_daily()
    # export_electricitymap()
