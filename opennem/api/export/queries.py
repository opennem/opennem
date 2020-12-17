from datetime import datetime, timedelta
from textwrap import dedent
from typing import List, Optional

from opennem.api.stats.controllers import get_scada_range, networks_to_in
from opennem.api.stats.schema import ScadaDateRange
from opennem.schema.network import NetworkSchema, NetworkWEM
from opennem.schema.time import TimeInterval, TimePeriod


def price_network_query(
    interval: TimeInterval,
    network: NetworkSchema = NetworkWEM,
    group_field: str = "bs.network_id",
    date_range: Optional[ScadaDateRange] = None,
    period: Optional[TimePeriod] = None,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:

    if not networks_query:
        networks_query = [network]

    if network not in networks_query:
        networks_query.append(network)

    if not date_range:
        date_range = get_scada_range(network=network, networks=networks_query)

    timezone = network.get_timezone(postgres_format=True)

    __query = """
        SET SESSION TIME ZONE '{timezone}';

        select
            time_bucket_gapfill('{trunc}', bs.trading_interval) AS trading_interval,
            {group_field},
            avg(bs.price) as price
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

    network_region_query = ""

    if network_region:
        network_region_query = f"bs.network_region='{network_region}' and "
        group_field = "bs.network_region"

    network_query = "bs.network_id IN ({}) and ".format(
        networks_to_in(networks_query)
    )

    if len(networks_query) > 1:
        group_field = "'AU'"

    if not date_range:
        raise Exception("Require a date range")

    date_max = date_range.get_end()
    date_min = date_range.get_start()

    if period:
        date_min = date_range.get_end() - timedelta(minutes=period.period)

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=interval.interval_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            group_field=group_field,
        )
    )

    return query


def power_network_fueltech_query(
    interval: TimeInterval,
    network: NetworkSchema = NetworkWEM,
    date_range: Optional[ScadaDateRange] = None,
    period: Optional[TimePeriod] = None,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:

    if not networks_query:
        networks_query = [network]

    if network not in networks_query:
        networks_query.append(network)

    if not date_range:
        date_range = get_scada_range(network=network, networks=networks_query)

    timezone = network.timezone_database

    __query = """
        select
            t.trading_interval at time zone '{timezone}',
            t.fueltech_code,
            sum(t.facility_power)
        from (
            select
                time_bucket_gapfill('{trunc}', fs.trading_interval) AS trading_interval,
                coalesce(avg(fs.generated), 0) as facility_power,
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
                {fueltech_filter}
            group by 1, 3, 4
        ) as t
        group by 1, 2
        order by 1 desc
    """

    network_region_query = ""
    fueltech_filter = ""

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "
    else:
        fueltech_filter = "and f.fueltech_id not in ('imports', 'exports')"

    network_query = "fs.network_id IN ({}) and ".format(
        networks_to_in(networks_query)
    )

    if not date_range:
        raise Exception("require a date range")

    date_max = date_range.get_end()
    date_min = date_range.get_start()

    if period:
        date_min = date_range.get_end() - timedelta(minutes=period.period)

    query = dedent(
        __query.format(
            network_query=network_query,
            trunc=interval.interval_sql,
            network_region_query=network_region_query,
            timezone=timezone,
            date_max=date_max,
            date_min=date_min,
            fueltech_filter=fueltech_filter,
        )
    )

    return query


def energy_network_fueltech_query(
    network: NetworkSchema,
    interval: Optional[TimeInterval] = None,
    year: Optional[int] = None,
    network_region: Optional[str] = None,
    networks_query: Optional[List[NetworkSchema]] = None,
) -> str:
    """
    Get Energy for a network or network + region
    based on a year
    """

    if not networks_query:
        networks_query = [network]

    if network not in networks_query:
        networks_query.append(network)

    __query = """
        select
            date_trunc('{trunc}', t.trading_interval at time zone '{timezone}') as trading_day,
            t.fueltech_id,
            sum(t.energy) / 1000 as fueltech_energy,
            sum(t.market_value) as fueltech_market_value,
            sum(t.emissions) as fueltech_emissions
        from
            (select
                time_bucket_gapfill('1 hour', fs.trading_interval) as trading_interval,
                f.fueltech_id,
                coalesce(
                    sum(eoi_quantity),
                    energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated))
                ) as energy,
                case when avg(bs.price) >= 0 then
                    coalesce(
                        sum(eoi_quantity) * avg(bs.price),
                        energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated)) * avg(bs.price),
                        0.0
                    )
                else null
                end as market_value,
                case when avg(f.emissions_factor_co2) >= 0 then
                    coalesce(
                        sum(eoi_quantity) * avg(f.emissions_factor_co2),
                        energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated)) * avg(f.emissions_factor_co2),
                        0.0
                    )
                else null
                end as emissions
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

    scada_range = get_scada_range(network=network, networks=networks_query)

    if not scada_range:
        raise Exception("Require a scada range for {}".format(network.code))

    network_region_query = ""
    fueltech_filter = ""

    if network_region:
        network_region_query = f"f.network_region='{network_region}' and "
    else:
        fueltech_filter = "and f.fueltech_id not in ('imports', 'exports')"

    network_query = "fs.network_id IN ({}) and ".format(
        networks_to_in(networks_query)
    )

    if not timezone:
        timezone = "UTC"

    trunc = None

    if interval:
        trunc = interval.trunc

    if year:
        # might have to do +offset times
        year_max = "{}-12-31 23:59:59{}".format(year, offset)
        year_min = "{}-01-01 00:00:00{}".format(year, offset)

        if year == datetime.now().year:
            year_max = scada_range.get_end()

        if not trunc:
            trunc = "day"
    else:
        year_min = scada_range.get_start()
        year_max = scada_range.get_end()

        if not trunc:
            trunc = "month"

    network_region_query = ""

    if network_region:
        network_region_query = f" f.network_region='{network_region}' and"

    query = dedent(
        __query.format(
            trunc=trunc,
            year_min=year_min,
            year_max=year_max,
            timezone=timezone,
            network_query=network_query,
            network_region_query=network_region_query,
            fueltech_filter=fueltech_filter,
        )
    )

    return query
