"""
Queries for network data

@TODO use sqlalchemy text() compiled queries
"""

from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

from opennem.controllers.output.schema import OpennemExportSeries
from opennem.queries.utils import duid_to_case


def power_facility_query(
    time_series: OpennemExportSeries,
    facility_codes: list[str],
) -> TextClause:
    __query = """
        select
            t.trading_interval at time zone '{timezone}',
            coalesce(avg(t.facility_power), 0),
            t.facility_code
        from (
            select
                time_bucket_gapfill('{trunc}', fs.trading_interval) AS trading_interval,
                coalesce(
                    avg(fs.generated), 0
                ) as facility_power,
                fs.facility_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            where
                fs.trading_interval <= '{date_max}' and
                fs.trading_interval >= '{date_min}' and
                fs.facility_code in ({facility_codes_parsed})
            group by 1, 3
        ) as t
        group by 1, 3
        order by 1 desc
    """

    date_range = time_series.get_range()

    query = __query.format(
        facility_codes_parsed=duid_to_case(facility_codes),
        trunc=time_series.interval.interval_sql,
        timezone=time_series.network.timezone_database,
        date_max=date_range.end,
        date_min=date_range.start,
    )

    return text(query)


def energy_facility_query(time_series: OpennemExportSeries, facility_codes: list[str]) -> TextClause:
    """
    Get Energy for a list of facility codes
    """

    __query = """
    select
        time_bucket_gapfill('{interval}', t.trading_day) as trading_day,
        t.facility_code,
        coalesce(sum(t.energy), 0) as fueltech_energy,
        coalesce(sum(t.market_value), 0) as fueltech_market_value,
        coalesce(sum(t.emissions), 0) as fueltech_emissions
    from at_facility_daily t
    where
        t.trading_day <= '{date_max}' and
        t.trading_day >= '{date_min}' and
        t.facility_code in ({facility_codes_parsed})
    group by 1, 2
    order by
        trading_day desc;
    """

    if time_series.interval.interval >= 10080:
        __query = """
        select
            date_trunc('{trunc}', t.trading_day) as trading_day,
            t.facility_code,
            sum(t.energy) as fueltech_energy,
            sum(t.market_value) as fueltech_market_value,
            sum(t.emissions) as fueltech_emissions
        from at_facility_daily t
        where
            t.trading_day <= '{date_max}' and
            t.trading_day >= '{date_min}' and
            t.facility_code in ({facility_codes_parsed})
        group by 1, 2
        order by
            trading_day desc;
        """

    date_range = time_series.get_range()

    return text(
        __query.format(
            facility_codes_parsed=duid_to_case(facility_codes),
            trunc=time_series.interval.trunc,
            interval=time_series.interval.interval_human,
            date_max=date_range.end.date(),
            date_min=date_range.start.date(),
            timezone=time_series.network.timezone_database,
        )
    )


def emission_factor_region_query(time_series: OpennemExportSeries, network_region_code: str | None = None) -> TextClause:
    # @TODO replace this with query from agg tables.
    __query = """
        select
            t.trading_interval at time zone '{timezone}',
            t.network_region,
            coalesce(sum(t.power), 0) as generated,
            coalesce(sum(t.emissions), 0) as emissions,
            case when sum(t.power) > 0 then
                sum(t.emissions) / sum(t.power)
            else 0
            end as emissions_factor
        from
        (
            select
                time_bucket_gapfill('{trunc}', fs.trading_interval) as trading_interval,
                f.network_region as network_region,
                coalesce(sum(fs.generated), 0) as power,
                coalesce(sum(fs.generated) * max(f.emissions_factor_co2), 0) as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            where
                fs.is_forecast is False and
                f.interconnector = False and
                f.network_id = '{network_id}' and
                fs.generated > 0 and
                {network_region_query}
                fs.trading_interval >= '{date_min}' and
                fs.trading_interval <= '{date_max}'
            group by
                1, f.code, 2
        ) as t
        group by 1, 2
        order by 1 asc, 2;
    """

    network_region_query = ""

    if network_region_code:
        network_region_query = f"f.network_region='{network_region_code}' and"

    date_range = time_series.get_range()

    return text(
        __query.format(
            network_region_query=network_region_query,
            network_id=time_series.network.code,
            trunc=time_series.interval.interval_human,
            date_max=date_range.end,
            date_min=date_range.start,
            timezone=time_series.network.timezone_database,
        )
    )


def network_fueltech_demand_query(time_series: OpennemExportSeries) -> TextClause:
    __query = """
        select
            fs.trading_interval at time zone '{tz}' as trading_interval,
            f.fueltech_id,
            round(sum(fs.eoi_quantity) / 1000, 2) as energy,
            sum(bs.demand_total) as demand
        from facility_scada fs
        left join balancing_summary bs on bs.trading_interval = fs.trading_interval and bs.network_id = fs.network_id
        left join facility f on fs.facility_code = f.code
        join fueltech ft on f.fueltech_id = ft.code
        where
            fs.trading_interval >= '{date_min}'
            and fs.trading_interval < '{date_max}'
            and fs.network_id = '{network_id}'
            and f.dispatch_type = 'GENERATOR'
        group by 1, 2;
    """

    date_range = time_series.get_range()

    date_min: datetime = date_range.end - timedelta(days=1)

    return text(
        __query.format(
            network_id=time_series.network.code,
            trunc=time_series.interval.trunc,
            date_max=date_range.end,
            date_min=date_min,
            tz=time_series.network.timezone_database,
        )
    )


def network_region_price_query(time_series: OpennemExportSeries, network_region_code: str | None = None) -> TextClause:
    __query = """
        select
            time_bucket('{trunc}', bs.trading_interval) as trading_interval,
            bs.network_id,
            bs.network_region,
            coalesce(avg(bs.price), avg(bs.price_dispatch)) as price
        from balancing_summary bs
        where
            bs.trading_interval >= '{date_min}'
            and bs.trading_interval <= '{date_max}'
            and bs.network_id = '{network_id}'
            {network_regions_query}
        group by 1, 2, 3;
    """

    date_range = time_series.get_range()

    date_min: datetime = date_range.end - timedelta(days=1)

    network_regions_query = ""

    if network_region_code:
        network_regions_query = f"and bs.network_region = '{network_region_code.upper()}'"

    return text(
        __query.format(
            network_id=time_series.network.code,
            trunc=time_series.interval.interval_human,
            date_max=date_range.end,
            date_min=date_min,
            network_regions_query=network_regions_query,
        )
    )
