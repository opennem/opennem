import logging
from datetime import datetime
from textwrap import dedent

from sqlalchemy import TextClause, text

from opennem.api.stats.controllers import networks_to_in
from opennem.controllers.output.schema import OpennemExportSeries
from opennem.queries.utils import list_to_case
from opennem.schema.network import NetworkAU, NetworkSchema, NetworkWEM

logger = logging.getLogger("opennem.queries.power")


def get_fueltech_generation_query(
    time_series: OpennemExportSeries,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> TextClause:
    """Query power stats"""

    if not networks_query:
        networks_query = [time_series.network]

    if time_series.network not in networks_query:
        networks_query.append(time_series.network)

    __query = """
    SELECT
        time_bucket_gapfill('{interval}', interval) as interval,
        fueltech_code,
        sum(generated) as fueltech_power,
        sum(emissions) as fueltech_emissions,
        case when
            sum(generated) > 0 then round(sum(emissions)::numeric / sum(generated)::numeric, 4)
            else 0
        end as fueltech_emissions_intensity
    FROM at_facility_intervals
    WHERE
        interval between '{date_min}' and '{date_max}' and
        {network_query}
        {network_region_query}
        fueltech_code not in ('solar_rooftop')
    group by 1, 2
    ORDER BY interval DESC, 2;
    """

    network_region_query: str = ""
    wem_apvi_case: str = ""

    if network_region:
        network_region_query = f"network_region='{network_region}' and "

    if NetworkWEM in networks_query:
        # silly single case we'll refactor out
        # APVI network is used to provide rooftop for WEM so we require it
        # in country-wide totals
        wem_apvi_case = "or (network_id='APVI' and network_region='WEM')"

    network_query = f"(network_id IN ({networks_to_in(networks_query)}) {wem_apvi_case}) and "

    # Get the data time range
    # use the new v2 feature if it has been provided otherwise use the old method
    time_series_range = time_series.get_range()
    date_max = time_series_range.end
    date_min = time_series_range.start

    # If we have a fueltech filter, add it to the query

    query = dedent(
        __query.format(
            interval=time_series.interval.interval_human,
            network_query=network_query,
            network_region_query=network_region_query,
            date_max=date_max,
            date_min=date_min,
            wem_apvi_case=wem_apvi_case,
        )
    )

    return text(query)


def get_rooftop_generation_query(
    network: NetworkSchema, date_start: datetime, date_end: datetime, network_region: str | None = None
) -> TextClause:
    """For a network and network region get the power by fueltech"""

    # network query filter
    networks = [i.code for i in network.subnetworks] if network.subnetworks else [network.code]

    if network == NetworkAU:
        networks.extend(["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL", "APVI"])

    network_query = f"and fs.network_id in ({list_to_case(networks)})"

    # network region query filter
    if network_region:
        network_region_query = f"and fs.network_region = '{network_region}'"
    else:
        network_region_query = ""

    # bucket size
    bucket_size = "5min"

    if network == NetworkAU:
        bucket_size = "30min"

    __query = f"""
        select
            time_bucket_gapfill('{bucket_size}', fs.interval) as interval,
            fueltech_code,
            interpolate(coalesce(sum(fs.generated), 0)) as generated,
            interpolate(coalesce(sum(fs.energy), 0)) as energy,
            interpolate(coalesce(sum(fs.market_value), 0)) as market_value
        from at_facility_intervals fs
        where
            (
                fs.network_id in ('AEMO_ROOFTOP', 'AEMO_ROOFTOP_BACKFILL') or
                (fs.network_id = 'APVI' and fs.network_region = 'WEM')
            )
            and fs.interval between '{date_start}' and '{date_end}'
            {network_query}
            {network_region_query}
        group by 1, 2
        order by 1 desc, 2;
    """

    return text(__query)


def get_rooftop_forecast_generation_query(
    network: NetworkSchema, date_start: datetime, date_end: datetime, network_region: str | None = None
) -> TextClause:
    """For a network and network region get rooftop forecast generation"""

    # network query filter
    networks = [i.code for i in network.subnetworks] if network.subnetworks else [network.code]

    if network == NetworkAU:
        networks.extend(["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL", "APVI"])

    network_query = f"and fs.network_id in ({list_to_case(networks)})"

    # network region query filter
    if network_region:
        network_region_query = f"and f.network_region = '{network_region}'"
    else:
        network_region_query = ""

    # bucket size
    bucket_size = "5min"

    if network == NetworkAU:
        bucket_size = "30min"

    __query = f"""
        select
            time_bucket_gapfill('{bucket_size}', fs.interval) as interval,
            u.fueltech_id,
            interpolate(coalesce(sum(fs.generated), 0)) as generated,
            interpolate(coalesce(sum(fs.energy), 0)) as energy
        from facility_scada fs
        join units u on fs.facility_code = u.code
        join facilities f on f.id = u.station_id
        where
            (
                fs.network_id in ('AEMO_ROOFTOP', 'AEMO_ROOFTOP_BACKFILL') or
                (fs.network_id = 'APVI' and f.network_region = 'WEM')
            )
            and fs.interval between '{date_start}' and '{date_end}'
            and fs.is_forecast = true
            {network_query}
            {network_region_query}
        group by 1, 2
        order by 1 desc, 2;
    """

    return text(__query)
