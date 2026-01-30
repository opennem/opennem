""" """

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import TextClause, text

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.db import get_read_session
from opennem.queries.utils import networks_to_sql_in
from opennem.schema.network import NetworkAPVI, NetworkAU, NetworkNEM, NetworkSchema, NetworkWEM, NetworkWEMDE

logger = logging.getLogger("opennem.queries.energy")


def get_energy_network_fueltech_query(
    time_series: OpennemExportSeries,
    network: NetworkSchema,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> TextClause:
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
        networks_query = [time_series.network] + (time_series.network.subnetworks or [])

    __query = """
    select
        time_bucket_gapfill('{trunc}', t.interval) as interval,
        t.fueltech_code,
        round((sum(t.energy) / 1000)::numeric, 4) as fueltech_energy_gwh,
        round(sum(t.market_value)::numeric, 2) as fueltech_market_value_dollars,
        round(sum(t.emissions)::numeric, 4) as fueltech_emissions
    from mv_fueltech_daily t
    where
        t.interval >= '{date_min}' and t.interval <= '{date_max}' and
        {network_query}
        {network_region_query}
        1=1
    group by 1, 2
    order by
        1 desc, 2;
    """

    network_region_query = ""

    # Get the time range using either the old way or the new v4 way
    time_series_range = time_series.get_range()

    if network_region:
        network_region_query = f"t.network_region='{network_region}' and"

    # @NOTE special case for WEM to only include APVI data for that network/region
    # and not double-count all of AU
    network_apvi_wem = ""

    if network in [NetworkWEM, NetworkAU]:
        network_apvi_wem = "or (t.network_id='APVI' and t.network_region in ('WEM'))"

        if NetworkAPVI in networks_query:
            networks_query.pop(networks_query.index(NetworkAPVI))

    networks_list = networks_to_sql_in(networks_query)

    network_query = f"(t.network_id IN ({networks_list}) {network_apvi_wem}) and "

    return text(
        __query.format(
            trunc=time_series_range.interval.interval_sql,
            date_min=time_series_range.start,
            date_max=time_series_range.end,
            network_query=network_query,
            network_region_query=network_region_query,
        )
    )


def get_energy_facility_query(time_series: OpennemExportSeries, facility_code: str) -> TextClause:
    """
    Get Energy for a facility code
    """
    __query = """
    SELECT
        time_bucket_gapfill('{interval}', interval) as interval,
        facility_code,
        unit_code,
        round(sum(energy)::numeric, 4) as energy,
        round(sum(emissions)::numeric, 4) as emissions,
        round(sum(market_value)::numeric, 4) as market_value
    FROM mv_facility_unit_daily
    WHERE
        facility_code = '{facility_code}' and
        interval >= '{date_min}' and interval <= '{date_max}'
    GROUP BY 1, 2, 3
    ORDER BY 1 DESC, 2, 3;
    """

    date_range = time_series.get_range()

    return text(
        __query.format(
            interval=time_series.interval.interval_sql,
            facility_code=facility_code,
            date_max=date_range.end.date(),
            date_min=date_range.start.date(),
        )
    )


# Queries used in record reactor


async def get_fueltech_interval_energy_emissions(
    network: NetworkSchema, interval: str, date_start: datetime, date_end: datetime, region_group: bool = False
) -> Any:
    """
    Get the total generated energy emissions for a network
    based an interval size

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


async def get_fueltech_generated_energy_emissions(
    network: NetworkSchema, interval: str, date_start: datetime, date_end: datetime, region_group: bool = False
) -> list[Any]:
    """
    Get the total generated energy emissions for a network
    based on a year

    :param network: The network to query
    :param interval: The interval to group by
    :param date_start: The start date
    :param date_end: The end date
    :param region_group: Whether to group by region
    :return: ScalarResult containing the query results
    """

    network_region_query = "fs.network_region as network_region," if region_group else ""
    group_by = "1,2,3,4" if region_group else "1,2,3"
    network_query = "'NEM','AEMO_ROOFTOP','AEMO_ROOFTOP_BACKFILL'" if network == NetworkNEM else "'WEM', 'APVI'"
    network_region_filter_query = "fs.network_region IN ('WEM', 'WEMDE') and " if network in [NetworkWEM, NetworkWEMDE] else ""

    query = text(
        f"""
            SELECT
                {interval} AS interval,
                '{network.code.upper()}' as network_id,
                {network_region_query}
                ftg.code as fueltech_id,
                sum(fs.generated) as fueltech_generated,
                sum(fs.energy) as fueltech_energy,
                sum(fs.emissions) as fueltech_emissions
            FROM
                mv_fueltech_daily fs
                JOIN fueltech ft ON fs.fueltech_code = ft.code
                JOIN fueltech_group ftg on ftg.code = ft.fueltech_group_id
            WHERE
                fs.network_id IN ({network_query}) AND
                {network_region_filter_query}
                fs.interval >= :date_start AND
                fs.interval < :date_end
            GROUP BY
                {group_by}
            ORDER BY
                1 DESC, 2, 3, 4
        """
    )

    async with get_read_session() as session:
        result = await session.execute(query, {"date_start": date_start, "date_end": date_end})
        results = result.fetchall()

    return results


def get_energy_network_fueltech_query_clickhouse(
    time_series: OpennemExportSeries,
    network: NetworkSchema,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> str:
    """
    Get Energy for a network or network + region from ClickHouse.
    Uses the fueltech_intervals_daily_mv materialized view for daily aggregations
    or raw unit_intervals for other time periods.

    :param network: The network to query
    :param time_series: The time series to query
    :param network_region: The network region to query
    :param networks_query: The networks to query
    """

    if not networks_query:
        networks_query = [time_series.network] + (time_series.network.subnetworks or [])

    # Get the time range
    time_series_range = time_series.get_range()

    # Determine which table/view to use based on interval
    interval_sql = time_series_range.interval.interval_sql

    # Always use unit_intervals directly and aggregate in query
    # The MVs (fueltech_intervals_mv, fueltech_intervals_daily_mv) have auto-population
    # issues that cause partial aggregations to overwrite complete backfilled data
    table_name = "unit_intervals"
    date_column = "interval"

    # Map interval to ClickHouse date functions
    if interval_sql == "1 day":
        interval_expr = "toDate(interval)"
    elif interval_sql == "1 month":
        interval_expr = "toStartOfMonth(interval)"
    elif interval_sql == "1 year":
        interval_expr = "toStartOfYear(interval)"
    elif interval_sql == "5 minutes":
        interval_expr = "toStartOfFiveMinute(interval)"
    elif interval_sql == "30 minutes":
        interval_expr = "toStartOfHalfHour(interval)"
    elif interval_sql == "1 hour":
        interval_expr = "toStartOfHour(interval)"
    else:
        interval_expr = "interval"

    # Build network filter
    networks_list = "', '".join([n.code for n in networks_query])
    network_query = f"network_id IN ('{networks_list}')"

    # Special case for WEM to include APVI data
    if network in [NetworkWEM, NetworkAU]:
        network_query += " OR (network_id='APVI' AND network_region='WEM')"
        # Remove APVI from the main list if it's there
        if NetworkAPVI in networks_query:
            networks_query.pop(networks_query.index(NetworkAPVI))

    # Build region filter
    network_region_query = ""
    if network_region:
        network_region_query = f" AND network_region='{network_region}'"

    # Format dates for ClickHouse - strip timezone info and ensure it's in the right format
    # ClickHouse expects 'YYYY-MM-DD HH:MM:SS' format without timezone
    start_str = (
        time_series_range.start.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(time_series_range.start, "strftime")
        else str(time_series_range.start).split("+")[0].split(".")[0]
    )
    end_str = (
        time_series_range.end.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(time_series_range.end, "strftime")
        else str(time_series_range.end).split("+")[0].split(".")[0]
    )

    # Build the query
    # NOTE: Exclude 'battery' fueltech to prevent double-counting with battery_charging/battery_discharging
    __query = f"""
    SELECT
        {interval_expr} as interval,
        fueltech_id as fueltech_code,
        round(sum(energy) / 1000, 4) as fueltech_energy_gwh,
        round(sum(market_value), 2) as fueltech_market_value_dollars,
        round(sum(emissions), 4) as fueltech_emissions
    FROM {table_name} FINAL
    WHERE
        {date_column} >= toDateTime('{start_str}')
        AND {date_column} <= toDateTime('{end_str}')
        AND ({network_query})
        AND fueltech_id NOT IN ('battery')
        {network_region_query}
    GROUP BY interval, fueltech_code
    ORDER BY interval DESC, fueltech_code
    """

    return __query


if __name__ == "__main__":

    async def main() -> None:
        """
        Main entry point for running get_fueltech_generated_energy_emissions
        for NetworkNEM on 2nd Feb 2024, from midnight to midnight.
        """
        network = NetworkNEM
        interval = "fs.trading_day"
        date_start = datetime(2024, 2, 2, 0, 0, 0)  # Midnight at the start of Feb 2
        date_end = datetime(2024, 2, 3, 0, 0, 0)  # Midnight at the start of Feb 3
        region_group = False

        try:
            results = await get_fueltech_generated_energy_emissions(
                network=network, interval=interval, date_start=date_start, date_end=date_end, region_group=region_group
            )

            print(f"Results for {network.code} from {date_start} to {date_end}:")

            # Convert ScalarResult to a list of dictionaries for datatable_print
            for r in results:
                print(r)
            # datatable_print(results)
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    asyncio.run(main())
