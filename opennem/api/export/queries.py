from datetime import datetime

from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import ScadaDateRange
from opennem.schema.network import NetworkWEM


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


def market_value_year_query(year: int, network_code: str = "WEM",) -> str:

    scada_range: ScadaDateRange = get_scada_range(network=NetworkWEM)

    __query = """
        SET SESSION TIME ZONE '+08';

        select
            time_bucket_gapfill('1 day', fs.trading_interval) AS trading_day,
            on_energy_sum(fs.eoi_quantity, '1 day') * avg(bs.price) as energy_interval,
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

    date_min = f"'{year}-01-01'"
    date_max = f"'{year}-12-31'"

    if year == datetime.now().year:
        date_max = scada_range.get_end_sql()

    if year == scada_range.start.year:
        date_min = scada_range.get_start_sql()

    query = __query.format(
        network_code=network_code, date_min=date_min, date_max=date_max,
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
                on_energy_sum(fs.generated, '1 day') * avg(bs.price) as energy_interval,
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
