from datetime import datetime, timedelta
from textwrap import dedent
from typing import Optional

from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import ScadaDateRange
from opennem.api.time import human_to_interval, human_to_period
from opennem.schema.network import NetworkSchema, NetworkWEM
from opennem.schema.time import TimeInterval, TimePeriod


def wem_demand_all(network_code: str = "WEM"):

    __query = """
        SET SESSION TIME ZONE '+08';

        select(
            date_trunc('month', t.trading_interval),
            t.price,
            t.generated
        ) from (
            select
                time_bucket_gapfill('1 day', bs.trading_interval,
                round(wbs.price, 2) as price,
                round(wbs.generation_total, 2) as generated
            from balancing_summary bs
            where bs.network_id='{network_code}'
        ) as t
        group by 1,
        order by 1 desc
    """

    query = __query.format(network_code=network_code)

    return query


def power_network_fueltech_query(
    interval: TimeInterval,
    network: NetworkSchema = NetworkWEM,
    period: TimePeriod = human_to_period("7d"),
    network_region: Optional[str] = None,
) -> str:

    scada_range: ScadaDateRange = get_scada_range(network=network)

    timezone = network.timezone_database

    __query = """
        select
            t.trading_interval at time zone '{timezone}',
            t.fueltech_code,
            sum(t.facility_power)
        from (
            select
                time_bucket_gapfill('{trunc}', trading_interval) AS trading_interval,
                coalesce(
                    avg(fs.generated), 0
                ) as facility_power,
                fs.facility_code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                fs.network_id='{network_code}'
                and f.fueltech_id is not null
                and fs.trading_interval <= '{date_max}'
                and fs.trading_interval > '{date_min}'
                {network_region_query}
            group by 1, 3, 4
        ) as t
        group by 1, 2
        order by 1 desc
    """

    network_region_query = ""

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    date_max = scada_range.get_end()
    date_min = scada_range.get_end() - timedelta(days=7)

    query = dedent(
        __query.format(
            network_code=network.code,
            trunc=interval.interval_sql,
            period=period.period_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
        )
    )

    return query


def energy_network_fueltech_daily_query(
    network: NetworkSchema,
    year: int,
    interval: TimeInterval,
    network_region: Optional[str] = None,
) -> str:
    """
        Get Energy for a network or network + region
        based on a year
    """

    __query = """
        select
            date_trunc('day', t.trading_interval at time zone '{timezone}') as trading_day,
            t.fueltech_id,
            energy_sum(t.generated, '1 day') * interval_size('1 day', count(t.generated)) / 1000 as facility_energy,
            energy_sum(t.generated, '1 day') * interval_size('1 day', count(t.generated)) * avg(t.price) as price
        from
            (select
                time_bucket_gapfill('{trunc}', fs.trading_interval) as trading_interval,
                f.fueltech_id,
                count(fs.generated) as sample_count,
                coalesce(avg(fs.generated), 0) as generated,
                coalesce(avg(bs.price), 0) as price
            from facility_scada fs
                left join facility f on fs.facility_code = f.code
                left join balancing_summary bs on
                    date_trunc('hour', bs.trading_interval) = date_trunc('hour', fs.trading_interval)
                    and bs.network_id='{network_code}'
            where
                fs.network_id='{network_code}'
                and f.fueltech_id is not null
                and fs.trading_interval <= '{year_max}'
                and fs.trading_interval >= '{year_min}'
                {network_region_query}
            group by
                1,
                f.code,
                f.fueltech_id
            ) as t
        group by 1, 2
        order by
            trading_day desc;
    """

    timezone = network.timezone_database
    offset = network.get_timezone(postgres_format=True)
    scada_range: ScadaDateRange = get_scada_range(network=network)

    if not timezone:
        timezone = "UTC"

    # might have to do +08 times
    year_max = "{}-12-31 23:59:59{}".format(year, offset)
    year_min = "{}-01-01 00:00:00{}".format(year, offset)

    if year == datetime.now().year:
        year_max = scada_range.get_end()

    network_region_query = ""

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    query = dedent(
        __query.format(
            network_code=network.code,
            trunc="{} minutes".format(network.interval_size),
            year_min=year_min,
            year_max=year_max,
            network_region_query=network_region_query,
            timezone=timezone,
        )
    )

    return query


def market_value_daily_query(
    year: int,
    network: NetworkSchema = NetworkWEM,
    network_region: Optional[str] = None,
) -> str:

    scada_range: ScadaDateRange = get_scada_range(network=network)

    __query = """
        SET SESSION TIME ZONE '+08';

        select
            time_bucket_gapfill('1 day', fs.trading_interval) AS trading_day,
            energy_sum(generated, '1 day') * interval_size('1 day', count(generated))  * avg(bs.price) as energy_interval,
            f.fueltech_id
        from facility_scada fs
        left join facility f on fs.facility_code = f.code
        join balancing_summary bs on fs.trading_interval::date = bs.trading_interval::date
        where
            f.fueltech_id is not null and
            fs.network_id='WEM' and
            fs.trading_interval <= {date_max} and
            fs.trading_interval >= {date_min}
        group by 1, f.fueltech_id
        order by 1 desc, 2 asc
    """

    network_region_query = ""

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    date_min = f"'{year}-01-01'"
    date_max = f"'{year}-12-31'"

    if year == datetime.now().year:
        date_max = scada_range.get_end_sql()

    if year == scada_range.start.year:
        date_min = scada_range.get_start_sql()

    query = __query.format(
        network_code=network.code,
        date_min=date_min,
        date_max=date_max,
        network_region_query=network_region_query,
    )

    return query


def wem_market_value_all_query(network_code: str = "WEM",) -> str:

    scada_range: ScadaDateRange = get_scada_range(network=NetworkWEM)

    __query = """
        SET SESSION TIME ZONE '+08';

        select
            date_trunc('month', t.trading_day),
            sum(t.energy_interval),
            t.fueltech_id
        from (
            select
                time_bucket_gapfill('1 day', fs.trading_interval) AS trading_day,
                energy_sum(generated, '1 day') * interval_size('1 day', count(generated)) * avg(bs.price) as energy_interval,
                f.fueltech_id
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            join balancing_summary bs on fs.trading_interval::date = bs.trading_interval::date
            where
                f.fueltech_id is not null and
                fs.network_id='{network_code}' and
                extract('year' from fs.trading_interval) = '2020' and
                fs.trading_interval <= {date_max} and
                fs.trading_interval >= {date_min}
            group by 1, 3
        ) as t
        group by 1, 3
        order by 1 desc, 3 asc;
    """

    query = __query.format(
        network_code=network_code,
        date_min=scada_range.get_start_sql(),
        date_max=scada_range.get_end_sql(),
    )

    return query
