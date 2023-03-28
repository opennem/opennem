""" Main module responsible for exporting (to static files) energy data

called from the controller and initiated by the scheduler
"""

import logging

# from opennem import settings
from opennem.api.export.controllers import energy_fueltech_daily
from opennem.api.export.map import StatType
from opennem.api.export.utils import write_output
from opennem.api.stats.controllers import get_scada_range_optimized
from opennem.api.stats.schema import ScadaDateRange
from opennem.api.time import human_to_interval, human_to_period
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.controllers.output.utils import get_export_output_path
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import get_today_opennem

# from datetime import datetime


logger = logging.getLogger("opennem.controllers.output.energy")


class OpennemOutputEnergyException(Exception):
    pass


def run_export_energy_all(network: NetworkSchema) -> None:
    """Run export for all regions

    :param network: The network to export
    """
    pass


def run_export_energy_for_year(network: NetworkSchema, year: int | None = None) -> None:
    """ """
    if not year:
        year = get_today_opennem().year

    date_range: ScadaDateRange = get_scada_range_optimized(network=network)

    if not date_range:
        raise OpennemOutputEnergyException(f"Could not get date range for energy {network.code} {year}")

    logger.debug(f"Date range is: {network.code} {date_range.start} => {date_range.end}")

    # Migrate to this time_series
    time_series = OpennemExportSeries(
        start=date_range.start,
        end=date_range.end,
        network=network,
        year=year,
        interval=human_to_interval("1d"),
        period=human_to_period("1Y"),
    )

    # 1. ENERGY
    stat_set = energy_fueltech_daily(
        time_series=time_series,
        networks_query=[],
        # network_region_code=energy_stat.network_region_query or energy_stat.network_region,
    )

    if not stat_set:
        raise OpennemOutputEnergyException(
            f"No result from energy_fueltech_daily for {network} " "{energy_stat.period} {energy_stat.network_region}"
        )

    # 2. DEMAND
    # demand_energy_and_value = demand_network_region_daily(
    #     time_series=time_series, network_region_code=energy_stat.network_region, networks=energy_stat.networks
    # )
    # stat_set.append_set(demand_energy_and_value)

    # 3. FLOWS

    # if network.has_interconnectors and energy_stat.network_region:
    #     if settings.flows_and_emissions_v2:
    #         interconnector_flows = energy_interconnector_flows_and_emissions_v2(
    #             time_series=time_series,
    #             network_region_code=energy_stat.network_region_query or energy_stat.network_region,
    #         )
    #         stat_set.append_set(interconnector_flows)
    #     else:
    #         interconnector_flows = energy_interconnector_region_daily(
    #             time_series=time_series,
    #             # networks_query=energy_stat.networks,
    #             network_region_code=energy_stat.network_region_query or energy_stat.network_region,
    #         )
    #         stat_set.append_set(interconnector_flows)

    #         interconnector_emissions = energy_interconnector_emissions_region_daily(
    #             time_series=time_series,
    #             networks_query=energy_stat.networks,
    #             network_region_code=energy_stat.network_region_query or energy_stat.network_region,
    #         )
    #         stat_set.append_set(interconnector_emissions)

    # 4. WEATHER

    # if energy_stat.bom_station:
    #     try:
    #         weather_stats = weather_daily(
    #             time_series=time_series,
    #             station_code=energy_stat.bom_station,
    #             network_region=energy_stat.network_region,
    #         )
    #         stat_set.append_set(weather_stats)
    #     except NoResults as e:
    #         logger.info(f"No results for weather result: {e}")
    #     except Exception as e:
    #         logger.error(f"weather_stat exception: {e}")

    s3_export_path = get_export_output_path(network=network, stat_type=StatType.energy, year=year)  # type: ignore

    write_output(s3_export_path, stat_set)


if __name__ == "__main__":
    run_export_energy_all(network=NetworkNEM)
