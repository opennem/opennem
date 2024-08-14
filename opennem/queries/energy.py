""" """

import logging
from datetime import datetime
from textwrap import dedent
from typing import Any

from sqlalchemy import text

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.db import get_read_session
from opennem.queries.utils import networks_to_sql_in
from opennem.schema.network import NetworkAPVI, NetworkAU, NetworkNEM, NetworkSchema, NetworkWEM, NetworkWEMDE

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


async def get_fueltech_generated_energy_emissions(
    network: NetworkSchema, interval: str, date_start: datetime, date_end: datetime, region_group: bool = False
) -> Any:
    """
    Get the total generated energy emissions for a network
    based on a year

    :param network: The network to query
    :param date_start: The start date
    :param date_end: The end date
    """

    network_region_query = "f.network_region as network_region," if region_group else ""
    group_by = "1,2,3,4" if region_group else "1,2,3"
    network_query = "'NEM','AEMO_ROOFTOP','AEMO_ROOFTOP_BACKFILL'" if network == NetworkNEM else "'WEM', 'WEMDE', 'APVI'"
    network_region_filter_query = "f.network_region IN ('WEM', 'WEMDE') and " if network in [NetworkWEM, NetworkWEMDE] else ""

    query = text(
        f"""
        SELECT
            time_bucket_gapfill('{interval}', interval) AS interval,
            f.network_id,
            {network_region_query}
            ftg.code AS fueltech_id,
            round(sum(fs.generated), 4) as fueltech_generated,
            round(sum(fs.energy), 4) as fueltech_energy,
            CASE
                WHEN sum(fs.energy) > 0 THEN round(sum(f.emissions_factor_co2 * fs.energy), 4)
                ELSE 0.0
            END AS fueltech_emissions,
            CASE
                WHEN sum(fs.energy) > 0 THEN round(sum(f.emissions_factor_co2 * fs.energy) / sum(fs.energy), 4)
                ELSE 0
            END AS fueltech_emissions_intensity
        FROM
            facility_scada fs
            JOIN facility f ON fs.facility_code = f.code
            JOIN fueltech ft ON f.fueltech_id = ft.code
            JOIN fueltech_group ftg ON ft.fueltech_group_id = ftg.code
        WHERE
            fs.is_forecast IS FALSE AND
            f.fueltech_id IS NOT NULL AND
            f.fueltech_id NOT IN ('imports', 'exports', 'interconnector') AND
            f.network_id IN ({network_query}) AND
            {network_region_filter_query}
            fs.interval >= :date_start AND
            fs.interval < :date_end
        GROUP BY
            {group_by}
        ORDER BY
            1 DESC, 2, 3;
    """
    )

    async with get_read_session() as session:
        result = await session.execute(query, {"date_start": date_start, "date_end": date_end})
        rows = result.fetchall()

    return rows
