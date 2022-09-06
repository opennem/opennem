"""
Tasks file to export JSONs of historic interval data for networks

For each network, this exports:

 - 5min (or network.interval_size) data in weekly buckets

This is called from the scheduler in opennem.workers.scheduler to run every morning
"""

import logging
from datetime import datetime, timedelta

from opennem.api.export.controllers import (
    demand_network_region_daily,
    emissions_for_network_interval,
    energy_interconnector_flows_and_emissions,
    power_week,
    weather_daily,
)
from opennem.api.export.utils import write_output
from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import ScadaDateRange
from opennem.api.time import human_to_period
from opennem.core.network_region_bom_station_map import get_network_region_weather_station
from opennem.db import get_scoped_session
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.dates import TimeSeries
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import (
    get_last_complete_day_for_network,
    get_today_opennem,
    get_week_number_from_datetime,
    week_series_datetimes,
)

logger = logging.getLogger("opennem.export.historic")


def export_network_intervals_for_week(
    week_start: datetime,
    week_end: datetime,
    network: NetworkSchema,
    network_region: NetworkRegion,
) -> int | None:
    """ """
    week_number = get_week_number_from_datetime(week_start)

    logging.info(
        "Exporting historic intervals for network {} and region {} and year {} and week {} ({} => {})".format(
            network.code, network_region.code, week_start.year, week_number, week_start, week_end
        )
    )

    if week_end > get_last_complete_day_for_network(network):
        week_end = get_last_complete_day_for_network(network)

    time_series = TimeSeries(
        start=week_start,
        end=week_end + timedelta(days=1),
        network=network,
        interval=network.get_interval(),
        period=human_to_period("7d"),
    )

    stat_set = power_week(
        time_series=time_series,
        networks_query=network.get_networks_query(),
        network_region_code=network_region.code,
    )

    if not stat_set:
        logger.error(
            "No historic intervals for network {} and region {} and year {} and week {} ({} => {})".format(
                network.code, network_region.code, week_start.year, week_number, week_start, week_end
            )
        )
        return None

    # emissions for network
    emission_intervals = emissions_for_network_interval(
        time_series=time_series, network_region_code=network_region.code
    )
    stat_set.append_set(emission_intervals)

    # demand and pricing
    demand_energy_and_value = demand_network_region_daily(
        time_series=time_series, network_region_code=network_region.code, networks=network.get_networks_query()
    )
    stat_set.append_set(demand_energy_and_value)

    # flows
    if network.has_interconnectors:
        interconnector_flows = energy_interconnector_flows_and_emissions(
            time_series=time_series,
            networks_query=network.get_networks_query(),
            network_region_code=network_region.code,
        )
        stat_set.append_set(interconnector_flows)

    # weather
    bom_station = get_network_region_weather_station(network_region.code)

    if bom_station:
        try:
            weather_stats = weather_daily(
                time_series=time_series, station_code=bom_station, network_region=network_region.code, network=network
            )
            stat_set.append_set(weather_stats)
        except Exception:
            pass

    # save out on s3 (or locally for dev)
    save_path = (
        f"v3/stats/historic/weekly/{network.code}/{network_region.code}/year/{week_start.year}/week/{week_number}.json"
    )

    written_bytes = write_output(save_path, stat_set)

    return written_bytes


def export_historic_intervals(
    limit: int | None = None,
    networks: list[NetworkSchema] = [NetworkNEM, NetworkWEM],
    network_region_code: str | None = None,
) -> None:
    """ """
    session = get_scoped_session()

    for network in networks:

        if not network.data_first_seen:
            raise Exception(f"Network {network.code} has no data first seen")

        # get the last complete day for the network
        network_last_complete_day = get_last_complete_day_for_network(network)
        network_last_completed_week_start = network_last_complete_day - timedelta(
            days=network_last_complete_day.weekday()
        )

        # query out the regions and filter
        query = session.query(NetworkRegion).filter(NetworkRegion.network_id == network.code)

        if network_region_code:
            query = query.filter(NetworkRegion.code == network_region_code)

        network_regions: list[NetworkRegion] = query.all()

        # loop through the networks
        for network_region in network_regions:
            for week_start, week_end in week_series_datetimes(
                start=network_last_completed_week_start, end=network.data_first_seen, length=limit
            ):
                try:
                    export_network_intervals_for_week(
                        week_start, week_end, network=network, network_region=network_region
                    )
                except Exception as e:
                    logger.error(f"export_historic_intervals error: {e}")


if __name__ == "__main__":
    export_historic_intervals(limit=1, networks=[NetworkNEM], network_region_code="NSW1")
