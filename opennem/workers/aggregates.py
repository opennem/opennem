""" Runs queries to populate the aggregate tables with facility data"""
import logging
import os
from datetime import datetime, timedelta
from textwrap import dedent

from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import ScadaDateRange
from opennem.db import get_database_engine
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import DATE_CURRENT_YEAR, get_today_nem

logger = logging.getLogger("opennem.workers.aggregates")

DRY_RUN = os.environ.get("DRY_RUN", False)


def aggregates_network_demand_query(date_max: datetime, date_min: datetime, network: NetworkSchema) -> str:
    """This query updates the aggregate demand table with market_value and energy"""

    __query = """
    insert into at_network_demand
        select
            date_trunc('day', fs.trading_interval at time zone n.timezone_database {network_interval_offset})
                as trading_day,
            fs.network_id,
            fs.network_region,
            sum(fs.energy) as demand_energy,
            sum(fs.market_value) as demand_market_value
        from (
            select
                time_bucket_gapfill('5 minutes', bs.trading_interval) as trading_interval,
                bs.network_id,
                bs.network_region,
                (sum(coalesce(bs.demand_total, bs.demand)) / {intervals_per_hour}) as energy,
                (sum(coalesce(bs.demand_total, bs.demand)) / {intervals_per_hour})
                    * max(bs.price_dispatch) * 1000 as market_value
            from balancing_summary bs
            where
                bs.network_id = '{network_id}'
                and bs.trading_interval >= '{date_min}'
                and bs.trading_interval <= '{date_max}'
            group by
                1, 2, 3
        ) as fs
        left join network n on fs.network_id = n.code
        group by
            1, 2, 3
    on conflict (trading_day, network_id, network_region) DO UPDATE set
            demand_energy = EXCLUDED.demand_energy,
            demand_market_value = EXCLUDED.demand_market_value;
    """

    date_min_offset = date_min.replace(tzinfo=network.get_fixed_offset(), microsecond=0)
    date_max_offset = date_max.replace(hour=0, minute=0, second=0, microsecond=0)

    if date_max_offset <= date_min_offset:
        raise Exception(
            f"aggregates_network_demand_query: date_max ({date_max_offset}) is before date_min ({date_min})"
        )

    network_interval_offset = ""

    if network.interval_shift:
        network_interval_offset = f" - interval '{network.interval_shift} minutes'"

    query = __query.format(
        network_interval_offset=network_interval_offset,
        date_min=date_min_offset,
        date_max=date_max_offset,
        network_id=network.code,
        intervals_per_hour=network.intervals_per_hour * 1000,
    )

    return dedent(query)


def aggregates_facility_daily_query(date_max: datetime, date_min: datetime, network: NetworkSchema) -> str:
    """This is the query to update the at_facility_daily aggregate"""

    __query = """
    insert into at_facility_daily
        select
            date_trunc('day', fs.trading_interval at time zone n.timezone_database) as trading_day,
            f.network_id,
            f.code as facility_code,
            f.fueltech_id,
            sum(fs.energy) as energy,
            sum(fs.market_value) as market_value,
            sum(fs.emissions) as emissions
        from (
            select
                time_bucket_gapfill('{network_interval_size} minutes', fs.trading_interval) as trading_interval,
                fs.facility_code as code,
                case
                    when sum(fs.eoi_quantity) > 0 then
                        coalesce(sum(fs.eoi_quantity), 0)
                    else 0
                end as energy,
                case
                    when sum(fs.eoi_quantity) > 0 then
                        coalesce(sum(fs.eoi_quantity), 0) * coalesce(max(bs.price_dispatch), max(bs.price), 0)
                    else 0
                end as market_value,
                case
                    when sum(fs.eoi_quantity) > 0 then
                        coalesce(sum(fs.eoi_quantity), 0) * coalesce(max(f.emissions_factor_co2), 0)
                    else 0
                end as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            left join balancing_summary bs on
                bs.trading_interval {trading_offset} = fs.trading_interval
                and bs.network_id = n.network_price
                and bs.network_region = f.network_region
                and f.network_id = '{network_id}'
            where
                fs.is_forecast is False
                and fs.network_id = '{network_id}'
                and fs.trading_interval >= '{date_min}'
                and fs.trading_interval < '{date_max}'
            group by
                1, 2
        ) as fs
        left join facility f on fs.code = f.code
        left join network n on f.network_id = n.code
        where
            f.fueltech_id is not null
        group by
            1,
            f.network_id,
            f.code,
            f.fueltech_id
    on conflict (trading_day, network_id, facility_code) DO UPDATE set
        energy = EXCLUDED.energy,
        market_value = EXCLUDED.market_value,
        emissions = EXCLUDED.emissions;
    """

    trading_offset = ""

    if network == NetworkNEM:
        trading_offset = "- INTERVAL '5 minutes'"

    date_min_offset = date_min.replace(tzinfo=network.get_fixed_offset(), microsecond=0)
    date_max_offset = (date_max + timedelta(days=1)).replace(tzinfo=network.get_fixed_offset(), microsecond=0)

    if date_max_offset <= date_min_offset:
        raise Exception(
            f"aggregates_facility_daily_query: date_max ({date_max_offset}) is before date_min ({date_min})"
        )

    query = __query.format(
        date_min=date_min_offset,
        date_max=date_max_offset,
        network_id=network.code,
        trading_offset=trading_offset,
        network_interval_size=network.interval_size,
    )

    return dedent(query)


def exec_aggregates_network_demand_query(date_min: datetime, date_max: datetime, network: NetworkSchema) -> bool:
    resp_code: bool = False
    engine = get_database_engine()
    result = None

    if date_max < date_min:
        raise Exception(
            f"exec_aggregates_network_demand_query: date_max ({date_max}) is prior to date_min ({date_min})"
        )

    query = aggregates_network_demand_query(date_min=date_min, date_max=date_max, network=network)

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            result = c.execute(query)

    logger.debug(result)

    return resp_code


def exec_aggregates_facility_daily_query(date_min: datetime, date_max: datetime, network: NetworkSchema) -> bool:
    resp_code: bool = False
    engine = get_database_engine()
    result = None

    # @TODO should put this check everywhere
    # or place it all in a schema that validates
    if date_max < date_min:
        raise Exception(
            f"exec_aggregates_facility_daily_query: date_max ({date_max}) is prior to date_min ({date_min})"
        )

    query = aggregates_facility_daily_query(date_min=date_min, date_max=date_max, network=network)

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            result = c.execute(query)

    logger.debug(result)

    # @NOTE rooftop fix for double counts
    if not DRY_RUN:
        run_rooftop_fix()

    return resp_code


def _get_year_range(year: int, network: NetworkSchema = NetworkNEM) -> tuple[datetime, datetime]:
    """Get a date range for a year with end exclusive"""
    tz = network.get_fixed_offset()

    date_min = datetime(year, 1, 1, 0, 0, 0, 0, tzinfo=tz)
    date_max = datetime(year + 1, 1, 1, 0, 0, 0, 0, tzinfo=tz)

    if year == DATE_CURRENT_YEAR:
        date_max = datetime.now().replace(hour=0, minute=0, second=0, tzinfo=tz)

    return date_min, date_max


def run_aggregates_demand_network() -> None:
    """Run the demand aggregates"""

    for network in [NetworkNEM, NetworkWEM]:

        if not network.data_first_seen:
            logger.error(f"run_aggregates_demand_network: Network {network.code} has no data_first_seen")
            continue

        exec_aggregates_network_demand_query(
            date_min=network.data_first_seen, date_max=get_today_nem(), network=network
        )


def run_aggregates_demand_network_days(days: int = 3) -> None:
    """Run the demand aggregates"""

    date_max = get_today_nem().replace(hour=0, minute=0, second=0, microsecond=0)
    date_min = date_max - timedelta(days=days)

    for network in [NetworkNEM, NetworkWEM]:
        exec_aggregates_network_demand_query(date_min=date_min, date_max=date_max, network=network)  # type: ignore


def run_aggregates_facility_year(year: int = DATE_CURRENT_YEAR, network: NetworkSchema = NetworkNEM) -> None:
    """Run aggregates for a single year

    Args:
        year (int, optional): [description]. Defaults to DATE_CURRENT_YEAR.
        network (NetworkSchema, optional): [description]. Defaults to NetworkNEM.
    """
    date_min, date_max = _get_year_range(year)
    logger.info(f"Running for year {year} - range : {date_min} {date_max}")

    exec_aggregates_facility_daily_query(date_min, date_max, network)


def run_aggregates_facility_all_by_year() -> None:
    YEAR_MIN = 1998
    YEAR_MAX = DATE_CURRENT_YEAR

    for year in range(YEAR_MAX, YEAR_MIN - 1, -1):
        run_aggregates_facility_year(year)


def run_aggregates_facility_all(network: NetworkSchema) -> None:
    scada_range: ScadaDateRange = get_scada_range(network=network)

    if not scada_range:
        logger.error(f"Could not find a scada range for {network.code}")
        return None

    exec_aggregates_facility_daily_query(date_min=scada_range.start, date_max=scada_range.end, network=network)


def run_aggregate_days(days: int = 1, network: NetworkSchema = NetworkNEM) -> None:
    """Run energy sum update for yesterday. This task is scheduled
    in scheduler/db"""

    # This is Sydney time as the data is published in local time

    # today_midnight in NEM time
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    date_max = today
    date_min = today - timedelta(days=days)

    exec_aggregates_facility_daily_query(date_min, date_max, network)


def run_rooftop_fix() -> None:
    query = "delete from at_facility_daily where trading_day < '2018-03-01 00:00:00+00' and network_id='AEMO_ROOFTOP';"

    engine = get_database_engine()

    with engine.connect() as c:
        logger.debug(query)

        if not DRY_RUN:
            c.execute(query)


def run_aggregates_all(
    networks: list[NetworkSchema] = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop],
) -> None:
    for network in networks:
        run_aggregates_facility_all(network)

    run_aggregates_demand_network()


def run_aggregates_all_days(
    days: int = 7,
    networks: list[NetworkSchema] = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop],
) -> None:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    date_end = today
    date_start = today - timedelta(days=days)

    for network in networks:
        logger.info(f"Running for Network {network.code} range {date_start} => {date_end}")
        exec_aggregates_facility_daily_query(date_min=date_start, date_max=date_end, network=network)

    run_aggregates_demand_network_days(days=days)


# Debug entry point
if __name__ == "__main__":
    # run_aggregates_all()
    # run_aggregates_demand_network()
    run_aggregates_facility_year(2022, network=NetworkNEM)
    # run_aggregates_demand_network_days(days=30)


def run_facility_aggregate_for_range() -> None:
    network = NetworkNEM
    date_start = datetime.fromisoformat("2022-01-01 00:00:00+10:00")
    date_end = date_start + timedelta(days=1)
    exec_aggregates_facility_daily_query(date_min=date_start, date_max=date_end, network=network)
