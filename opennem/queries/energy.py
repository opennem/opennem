""" """

import logging
from textwrap import dedent

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.queries.utils import networks_to_sql_in
from opennem.schema.network import NetworkAPVI, NetworkAU, NetworkSchema, NetworkWEM

logger = logging.getLogger("opennem.queries.energy")


def energy_network_fueltech_query(
    network: NetworkSchema,
    time_series: OpennemExportSeries,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
    coalesce_with: int | None = None,
) -> str:
    """
    Get Energy for a network or network + region
    based on a year

    :param network: The network to query
    :param time_series: The time series to query
    :param network_region: The network region to query
    :param sub_networks: The sub networks to query
    :param coalesce_with: The value to coalesce with
    """

    if not networks_query:
        networks_query = [time_series.network]

    __query = """
    select
        date_trunc('{trunc}', t.trading_day) as trading_day,
        t.network_id,
        t.network_region,
        t.fueltech_id,
        coalesce(sum(t.energy) / 1000, {coalesce_with}) as fueltech_energy_gwh,
        coalesce(sum(t.market_value), {coalesce_with}) as fueltech_market_value_dollars,
        coalesce(sum(t.emissions), {coalesce_with}) as fueltech_emissions_factor
    from at_facility_daily t
    left join facility f on t.facility_code = f.code
    where
        t.trading_day <= '{date_max}'::date and
        t.trading_day >= '{date_min}'::date and
        t.fueltech_id not in ('imports', 'exports', 'interconnector') and
        {network_query}
        {network_region_query}
        1=1
    group by 1, 2, 3, 4
    order by
        1 desc, 2;

    """

    network_region_query = ""

    # Get the time range using either the old way or the new v4 way
    time_series_range = time_series.get_range()
    date_max = time_series_range.end
    date_min = time_series_range.start

    trunc = time_series_range.interval.trunc

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and"

    # @NOTE special case for WEM to only include APVI data for that network/region
    # and not double-count all of AU
    network_apvi_wem = ""

    if network in [NetworkWEM, NetworkAU]:
        network_apvi_wem = "or (t.network_id='APVI' and f.network_region in ('WEM'))"

        if NetworkAPVI in networks_query:
            networks_query.pop(networks_query.index(NetworkAPVI))

    networks_list = networks_to_sql_in(networks_query)

    network_query = f"(t.network_id IN ({networks_list}) {network_apvi_wem}) and "

    return dedent(
        __query.format(
            trunc=trunc,
            date_min=date_min,
            date_max=date_max,
            network_query=network_query,
            network_region_query=network_region_query,
            coalesce_with=coalesce_with or "NULL",
        )
    )
