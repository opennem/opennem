"""Power generation queries — ClickHouse + PostgreSQL rooftop"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import TextClause, text

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.queries.utils import list_to_case
from opennem.schema.network import NetworkAPVI, NetworkAU, NetworkSchema, NetworkWEM

logger = logging.getLogger("opennem.queries.power")


def _fmt_ch(dt: object) -> str:
    """Format datetime for ClickHouse, stripping timezone."""
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt).split("+")[0]


def get_fueltech_power_query_clickhouse(
    time_series: OpennemExportSeries,
    network_region: str | None = None,
    networks_query: list[NetworkSchema] | None = None,
) -> str:
    """Fueltech generation + emissions from ClickHouse fueltech_intervals_mv.

    Returns: interval, fueltech_code, power, emissions, emissions_intensity.
    Excludes solar_rooftop (handled separately by rooftop queries).
    """
    if not networks_query:
        networks_query = [time_series.network] + (time_series.network.subnetworks or [])

    time_series_range = time_series.get_range()
    interval_sql = time_series_range.interval.interval_sql

    # Table and interval expression
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

    # Network filter
    networks_list = "', '".join([n.code for n in networks_query])
    network_query = f"network_id IN ('{networks_list}')"

    if time_series.network in [NetworkWEM, NetworkAU]:
        network_query += " OR (network_id='APVI' AND network_region='WEM')"
        if NetworkAPVI in networks_query:
            networks_query.remove(NetworkAPVI)

    region_filter = f" AND network_region='{network_region}'" if network_region else ""
    start_str = _fmt_ch(time_series_range.start)
    end_str = _fmt_ch(time_series_range.end)

    return f"""
    SELECT
        {interval_expr} as interval,
        fueltech_id as fueltech_code,
        round(sum(generated), 4) as fueltech_power,
        round(sum(emissions), 4) as fueltech_emissions,
        round(sum(emissions) / nullIf(sum(generated), 0), 4) as fueltech_emissions_intensity
    FROM {table_name} FINAL
    WHERE
        {date_column} >= toDateTime('{start_str}')
        AND {date_column} <= toDateTime('{end_str}')
        AND ({network_query})
        AND fueltech_id NOT IN ('solar_rooftop')
        {region_filter}
    GROUP BY interval, fueltech_code
    ORDER BY interval DESC, fueltech_code
    """


# --- Rooftop queries — stay on PostgreSQL facility_scada ---


def get_rooftop_forecast_generation_query(
    network: NetworkSchema,
    date_start: datetime,
    date_end: datetime,
    network_region: str | None = None,
) -> TextClause:
    """Rooftop forecast generation from PostgreSQL facility_scada."""
    networks = [i.code for i in network.subnetworks] if network.subnetworks else [network.code]
    if network == NetworkAU:
        networks.extend(["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL", "APVI"])

    network_query = f"and fs.network_id in ({list_to_case(networks)})"
    region_q = f"and f.network_region = '{network_region}'" if network_region else ""
    bucket = "30min" if network == NetworkAU else "5min"

    return text(f"""
        select
            time_bucket_gapfill('{bucket}', fs.interval) as interval,
            u.fueltech_id,
            interpolate(coalesce(sum(fs.generated), 0)) as generated,
            interpolate(coalesce(sum(fs.energy), 0)) as energy
        from facility_scada fs
        join units u on fs.facility_code = u.code
        join facilities f on f.id = u.station_id
        where
            (fs.network_id in ('AEMO_ROOFTOP', 'AEMO_ROOFTOP_BACKFILL')
             or (fs.network_id = 'APVI' and f.network_region = 'WEM'))
            and fs.interval between '{date_start}' and '{date_end}'
            and fs.is_forecast = true
            {network_query} {region_q}
        group by 1, 2
        order by 1 desc, 2;
    """)


def get_rooftop_generation_combined_query(
    network: NetworkSchema,
    date_start: datetime,
    date_end: datetime,
    network_region: str | None = None,
) -> TextClause:
    """Combined rooftop actual+forecast, preferring actual over forecast."""
    minutes = date_end.minute
    if minutes % 30 != 0:
        date_end = date_end + timedelta(minutes=30 - (minutes % 30))

    networks = [i.code for i in network.subnetworks] if network.subnetworks else [network.code]
    if network == NetworkAU:
        networks.extend(["AEMO_ROOFTOP", "AEMO_ROOFTOP_BACKFILL", "APVI"])

    network_query = f"network_id in ({list_to_case(networks)})"
    region_q = f"and network_region = '{network_region}'" if network_region else ""
    bucket = "30min" if network == NetworkAU else "5min"

    return text(f"""
    WITH rooftop_data AS (
        SELECT time_bucket('30min', fs.interval) as interval,
            f.network_id, f.network_region, fs.is_forecast,
            max(fs.generated) as generated, max(fs.energy) as energy
        FROM facility_scada fs
        JOIN units u on fs.facility_code = u.code
        JOIN facilities f on u.station_id = f.id
        WHERE fs.interval between '{date_start}' and '{date_end}'
            and (f.network_id IN ('AEMO_ROOFTOP', 'AEMO_ROOFTOP_BACKFILL')
                 OR (f.network_id = 'APVI' AND f.network_region = 'WEM'))
        GROUP BY 1, 2, 3, 4
    ),
    combined_data AS (
        SELECT interval, network_id, network_region,
            COALESCE(MAX(CASE WHEN NOT is_forecast THEN generated END),
                     MAX(CASE WHEN is_forecast THEN generated END)) as generated,
            COALESCE(MAX(CASE WHEN NOT is_forecast THEN energy END),
                     MAX(CASE WHEN is_forecast THEN energy END)) as energy,
            CASE WHEN MAX(CASE WHEN NOT is_forecast THEN 1 END) = 1 THEN false
                 WHEN MAX(CASE WHEN is_forecast THEN 1 END) = 1 THEN true
                 ELSE null END as is_forecast
        FROM rooftop_data GROUP BY 1, 2, 3
    )
    SELECT time_bucket_gapfill('{bucket}', interval) as interval,
        'solar_rooftop' as fueltech_id,
        interpolate(sum(generated)) as generated,
        interpolate(sum(energy)) as energy,
        bool_or(is_forecast) as is_forecast
    FROM combined_data
    WHERE interval between '{date_start}' and '{date_end}'
        and {network_query} {region_q}
    GROUP BY 1, 2
    ORDER BY interval DESC;
    """)
