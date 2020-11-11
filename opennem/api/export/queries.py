from datetime import datetime, timedelta
from textwrap import dedent
from typing import List, Optional

from opennem.api.stats.controllers import get_scada_range, networks_to_in
from opennem.api.stats.schema import ScadaDateRange
from opennem.api.time import human_to_period
from opennem.schema.network import NetworkSchema, NetworkWEM
from opennem.schema.time import TimeInterval, TimePeriod


def price_network_query(
    interval: TimeInterval,
    network: NetworkSchema = NetworkWEM,
    period: TimePeriod = human_to_period("7d"),
    network_region: Optional[str] = None,
    networks: Optional[List[NetworkSchema]] = None,
) -> str:

    scada_range: ScadaDateRange = get_scada_range(
        network=network, networks=networks
    )

    timezone = network.get_timezone(postgres_format=True)

    __query = """
        SET SESSION TIME ZONE '{timezone}';

        select
            time_bucket_gapfill('{trunc}', bs.trading_interval) AS trading_interval,
            bs.network_region,
            coalesce(avg(bs.price), 0) as price
        from balancing_summary bs
        where
            bs.trading_interval <= '{date_max}' and
            bs.trading_interval >= '{date_min}' and
            {network_query}
            {network_region_query}
            1=1
        group by 1, 2
        order by 1 desc
    """

    network_query = ""
    network_region_query = ""

    if network_region:
        network_region_query = f"bs.network_region='{network_region}' and "

    if network:
        network_query = f"bs.network_id = '{network.code}' and "

    if networks:
        network_query = "bs.network_id IN ({}) and ".format(
            networks_to_in(networks)
        )

    date_max = scada_range.get_end()
    date_min = scada_range.get_end() - timedelta(days=7)

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=interval.interval_sql,
            period=period.period_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
        )
    )

    return query


def power_network_fueltech_query(
    interval: TimeInterval,
    network: NetworkSchema = NetworkWEM,
    period: TimePeriod = human_to_period("7d"),
    network_region: Optional[str] = None,
    networks: Optional[List[NetworkSchema]] = None,
) -> str:

    scada_range: ScadaDateRange = get_scada_range(
        network=network, networks=networks
    )

    timezone = network.timezone_database

    __query = """
        select
            t.trading_interval at time zone '{timezone}',
            t.fueltech_code,
            sum(t.facility_power)
        from (
            select
                time_bucket_gapfill('{trunc}', fs.trading_interval) AS trading_interval,
                coalesce(
                    avg(fs.generated), 0
                ) as facility_power,
                fs.facility_code,
                ft.code as fueltech_code
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            join fueltech ft on f.fueltech_id = ft.code
            where
                f.fueltech_id is not null and
                {network_query}
                {network_region_query}
                fs.trading_interval <= '{date_max}' and
                fs.trading_interval > '{date_min}'
            group by 1, 3, 4
        ) as t
        group by 1, 2
        order by 1 desc
    """

    network_query = ""
    network_region_query = ""

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "

    if network:
        network_query = f"f.network_id = '{network.code}' and "

    if networks:
        network_query = "f.network_id IN ({}) and ".format(
            networks_to_in(networks)
        )

    date_max = scada_range.get_end()
    date_min = scada_range.get_end() - timedelta(days=7)

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=interval.interval_sql,
            period=period.period_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
        )
    )

    return query


def energy_network_fueltech_query(
    network: NetworkSchema,
    year: Optional[int] = None,
    get_all: bool = False,
    network_region: Optional[str] = None,
    networks: Optional[List[NetworkSchema]] = None,
) -> str:
    """
        Get Energy for a network or network + region
        based on a year
    """

    __query = """
        select
            date_trunc('{trunc}', t.trading_interval at time zone '{timezone}') as trading_day,
            t.fueltech_id,
            sum(t.energy) / 1000 as fueltech_energy,
            sum(t.market_value) as fueltech_market_value
        from
            (select
                time_bucket_gapfill('1 hour', fs.trading_interval) as trading_interval,
                f.fueltech_id,
                coalesce(
                    sum(eoi_quantity),
                    energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated))
                ) as energy,
                case when avg(bs.price) > 0 then
                    coalesce(
                        sum(eoi_quantity) * avg(bs.price),
                        energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated)) * avg(bs.price),
                        NULL
                    )
                else null
                end as market_value
            from facility_scada fs
                left join facility f on fs.facility_code = f.code
                left join balancing_summary bs on
                    bs.trading_interval = fs.trading_interval
                    and bs.network_id=fs.network_id
                    and bs.network_region = f.network_region
            where
                f.fueltech_id is not null and
                fs.trading_interval <= '{year_max}' and
                fs.trading_interval >= '{year_min}' and
                {network_query}
                {network_region_query}
                1=1
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
    scada_range: ScadaDateRange = get_scada_range(
        network=network, networks=networks
    )

    network_query = ""
    network_region_query = ""

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "

    if network:
        network_query = f"fs.network_id = '{network.code}' and "

    if networks:
        network_query = "fs.network_id IN ({}) and ".format(
            networks_to_in(networks)
        )

    if not timezone:
        timezone = "UTC"

    if year:
        # might have to do +08 times
        year_max = "{}-12-31 23:59:59{}".format(year, offset)
        year_min = "{}-01-01 00:00:00{}".format(year, offset)

        if year == datetime.now().year:
            year_max = scada_range.get_end()

        trunc = "day"
    else:
        year_min = scada_range.get_start()
        year_max = scada_range.get_end()
        trunc = "month"

    network_region_query = ""

    if network_region:
        network_region_query = f"and f.network_region='{network_region}'"

    query = dedent(
        __query.format(
            trunc=trunc,
            year_min=year_min,
            year_max=year_max,
            timezone=timezone,
            network_query=network_query,
            network_region_query=network_region_query,
        )
    )

    return query
