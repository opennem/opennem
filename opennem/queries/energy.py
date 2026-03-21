"""Energy queries — ClickHouse only"""

import logging

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.schema.network import NetworkAPVI, NetworkAU, NetworkSchema, NetworkWEM

logger = logging.getLogger("opennem.queries.energy")


def get_energy_network_fueltech_query_clickhouse(
    time_series: OpennemExportSeries,
    network: NetworkSchema,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> str:
    """
    Get Energy for a network or network + region from ClickHouse.
    Uses fueltech_intervals_daily_mv for daily+ or fueltech_intervals_mv for sub-daily.
    """

    if not networks_query:
        networks_query = [time_series.network] + (time_series.network.subnetworks or [])

    time_series_range = time_series.get_range()
    interval_sql = time_series_range.interval.interval_sql

    if interval_sql in ["1 day", "1 month", "1 year"]:
        table_name = "fueltech_intervals_daily_mv"
        date_column = "date"
        interval_expr = {
            "1 month": "toStartOfMonth(date)",
            "1 year": "toStartOfYear(date)",
        }.get(interval_sql, "date")
    else:
        table_name = "fueltech_intervals_mv"
        date_column = "interval"
        interval_expr = {
            "5 minutes": "toStartOfFiveMinute(interval)",
            "30 minutes": "toStartOfHalfHour(interval)",
            "1 hour": "toStartOfHour(interval)",
        }.get(interval_sql, "interval")

    networks_list = "', '".join([n.code for n in networks_query])
    network_query = f"network_id IN ('{networks_list}')"

    if network in [NetworkWEM, NetworkAU]:
        network_query += " OR (network_id='APVI' AND network_region='WEM')"
        if NetworkAPVI in networks_query:
            networks_query.remove(NetworkAPVI)

    network_region_query = f" AND network_region='{network_region}'" if network_region else ""

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

    return f"""
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
