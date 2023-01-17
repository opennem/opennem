"""
Tasks file to export JSONs of historic interval data for networks

For each network, this exports:

 - 5min (or network.interval_size) data in weekly buckets

This is called from the scheduler in opennem.workers.scheduler to run every morning
"""

import logging
from datetime import datetime, timedelta

from opennem import settings
from opennem.api.export.controllers import (
    demand_week,
    network_flows_for_region,
    power_and_emissions_for_network_interval,
    price_for_network_interval,
    weather_daily,
)
from opennem.api.export.utils import write_output
from opennem.api.time import human_to_interval, human_to_period
from opennem.clients.slack import slack_message
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.core.network_region_bom_station_map import get_network_region_weather_station
from opennem.db import get_scoped_session
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import (
    get_last_complete_day_for_network,
    get_week_number_from_datetime,
    get_week_start_from_week_num,
    week_series_datetimes,
)

logger = logging.getLogger("opennem.export.historic")


class ExporterHistoricException(Exception):
    """Specific exception for this worker"""

    pass


def export_network_intervals_for_week(
    week_start: datetime,
    week_end: datetime,
    network: NetworkSchema,
    network_region: NetworkRegion,
    week_number: int | None = None,
) -> int | None:
    """ """

    if not week_number:
        week_number = get_week_number_from_datetime(week_start)

    logging.info(
        f"Exporting historic intervals for network {network.code} and region "
        f"{network_region.code} and year {week_start.year} and week {week_number} ({week_start} => {week_end})"
    )

    if week_end > get_last_complete_day_for_network(network):
        week_end = get_last_complete_day_for_network(network)

    # time_range is a v4 feature
    time_series = OpennemExportSeries(
        start=week_start,
        end=week_end + timedelta(days=1),
        network=network,
        interval=network.get_interval(),
        period=human_to_period("7d"),
    )

    # power and emissions for network
    stat_set = power_and_emissions_for_network_interval(
        time_series=time_series, network_region_code=network_region.code, include_emission_factors=True
    )

    if not stat_set:
        logger.error(
            f"No historic intervals for network {network.code} and region "
            f"{network_region.code} and year {week_start.year} and week {week_number} ({week_start} => {week_end})"
        )

        return None

    # demand
    # adjust interval size
    time_series.interval = human_to_interval("30m")
    demand_energy_and_value = demand_week(time_series=time_series, network_region_code=network_region.code)
    stat_set.append_set(demand_energy_and_value)

    # pricing
    time_series.interval = human_to_interval("5m")
    price_for_network = price_for_network_interval(time_series=time_series, network_region_code=network_region.code)
    stat_set.append_set(price_for_network)

    # flows
    if network.has_interconnectors:
        interconnector_flows = network_flows_for_region(
            time_series=time_series,
            network_region_code=network_region.code,
            include_emissions=True,
            include_emission_factors=settings.debug,  # only on dev
        )

        # if not interconnector_flows:
        # raise ExporterHistoricException("No interconnector flows")

        stat_set.append_set(interconnector_flows)

    # weather
    bom_station = get_network_region_weather_station(network_region.code)

    if not bom_station:
        raise ExporterHistoricException(f"No weather station found for {network_region.code}")

    time_series.interval = human_to_interval("30m")
    try:
        weather_stats = weather_daily(
            time_series=time_series,
            station_code=bom_station,
            unit_name="temperature",
            network_region=network_region.code,
            network=network,
            include_min_max=False,
        )
        stat_set.append_set(weather_stats)
    except Exception as e:
        logger.error(f"Error getting weather stats for {network_region.code}: {e}")

    # save out on s3 (or locally for dev)
    save_path = f"v3/stats/historic/weekly/{network.code}/{network_region.code}/year/{week_start.year}/week/{week_number}.json"

    return write_output(save_path, stat_set)


def export_historic_intervals(
    limit: int | None = None, networks: list[NetworkSchema] = [], network_region_code: str | None = None
) -> None:
    """ """
    if networks is None:
        networks = [NetworkNEM, NetworkWEM]

    session = get_scoped_session()

    for network in networks:

        if not network.data_first_seen:
            raise ExporterHistoricException(f"Network {network.code} has no data first seen")

        # get the last complete day for the network
        network_last_complete_day = get_last_complete_day_for_network(network)
        network_last_completed_week_start = network_last_complete_day - timedelta(days=network_last_complete_day.weekday())

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
                if week_end > network_last_complete_day:
                    week_end = network_last_complete_day

                try:
                    export_network_intervals_for_week(week_start, week_end, network=network, network_region=network_region)
                except Exception as e:
                    raise ExporterHistoricException(f"export_historic_intervals error: {e}")

            slack_message(
                f"Ran historic interval export for {network} in {network_region.code} for date range {network.data_first_seen}"
                f" => {network_last_completed_week_start}"
            )


def export_historic_for_year_and_week_no(
    year: int, week_no: int, networks: list[NetworkSchema], network_region_code: str | None = None
) -> None:
    """Export historic intervals for a particular year and week"""
    session = get_scoped_session()

    network_codes = ", ".join([n.code for n in networks])
    logger.debug(f"Exporting historic for year {year} and week {week_no} and networks {network_codes}")

    for network in networks:
        week_start = get_week_start_from_week_num(year, week_no).astimezone(network.get_timezone())  # type: ignore
        week_end = week_start + timedelta(days=6)

        # query out the regions and filter
        query = session.query(NetworkRegion).filter(NetworkRegion.network_id == network.code)

        if network_region_code:
            query = query.filter(NetworkRegion.code == network_region_code)

        network_regions: list[NetworkRegion] = query.all()

        for network_region in network_regions:
            export_network_intervals_for_week(
                week_start, week_end, network=network, network_region=network_region, week_number=week_no
            )


if __name__ == "__main__":
    # export_historic_intervals(limit=52 * 2)
    export_historic_intervals()
    # export_historic_for_year_and_week_no(2022, 36, [NetworkNEM], network_region_code="NSW1")
