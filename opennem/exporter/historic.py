"""
Tasks file to export JSONs of historic interval data for networks

For each network, this exports:

 - 5min (or network.interval_size) data in weekly buckets

This is called from the scheduler in opennem.workers.scheduler to run every morning
"""

import logging
from datetime import timedelta

from opennem.api.export.controllers import (
    demand_network_region_daily,
    energy_fueltech_daily,
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
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkWEM
from opennem.utils.dates import get_today_opennem, get_week_number_from_datetime, week_series_datetimes

logger = logging.getLogger("opennem.export.historic")


def export_historic_intervals(limit: int | None = None) -> None:
    session = get_scoped_session()

    networks = [NetworkNEM, NetworkWEM]

    for network in networks:
        network_regions = session.query(NetworkRegion).filter(NetworkRegion.network_id == network.code).all()

        for network_region in network_regions:
            networks = []

            if network_region.code == "WEM":
                networks = [NetworkWEM, NetworkAPVI]

            if network == NetworkNEM:
                networks = [NetworkNEM, NetworkAEMORooftop]

            scada_range: ScadaDateRange = get_scada_range(network=network, networks=networks, energy=False)

            if not scada_range or not scada_range.start:
                logger.error("Could not get scada range for network {} and energy {}".format(network, True))
                continue

            for week_start, week_end in week_series_datetimes(
                start=scada_range.end, end=scada_range.start, length=limit
            ):
                week_number = get_week_number_from_datetime(week_start)

                if week_start > get_today_opennem():
                    continue

                logging.info(
                    "Exporting historic intervals for network {} and region {} and year {} and week {} ({} => {})".format(
                        network.code, network_region.code, week_start.year, week_number, week_start, week_end
                    )
                )

                time_series = TimeSeries(
                    start=week_start,
                    end=week_end + timedelta(days=1),
                    network=network,
                    interval=network.get_interval(),
                    period=human_to_period("7d"),
                )

                stat_set = power_week(
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

                if network == NetworkNEM:
                    interconnector_flows = energy_interconnector_flows_and_emissions(
                        time_series=time_series,
                        networks_query=networks,
                        network_region_code=network_region.code,
                    )
                    stat_set.append_set(interconnector_flows)

                bom_station = get_network_region_weather_station(network_region.code)

                if bom_station:
                    try:
                        weather_stats = weather_daily(
                            time_series=time_series,
                            station_code=bom_station,
                            network_region=network_region.code,
                        )
                        stat_set.append_set(weather_stats)
                    except Exception:
                        pass

                save_path = f"v3/stats/historic/weekly/{network.code}/{network_region.code}/year/{week_start.year}/week/{week_number}.json"

                logger.info(f"Will save to {save_path}")

                write_output(save_path, stat_set)


if __name__ == "__main__":
    export_historic_intervals(limit=52)
