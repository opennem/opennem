""" Runs queries to populate the aggregate tables with facility data

This populated the at_network_demand aggregate table with demand data.
"""
import logging
from datetime import datetime, timedelta
from textwrap import dedent

from opennem import settings
from opennem.db import get_database_engine
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import get_today_nem

logger = logging.getLogger("opennem.aggregates.demand")


class AggregateDemandException(Exception):
    """Exception that is raised when there is an error in the demand aggregate"""

    pass


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
        raise AggregateDemandException(
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


def exec_aggregates_network_demand_query(date_min: datetime, date_max: datetime, network: NetworkSchema) -> bool:
    engine = get_database_engine()
    result = None

    if date_max < date_min:
        raise AggregateDemandException(
            f"exec_aggregates_network_demand_query: date_max ({date_max}) is prior to date_min ({date_min})"
        )

    query = aggregates_network_demand_query(date_min=date_min, date_max=date_max, network=network)

    with engine.connect() as c:
        logger.debug(query)

        if not settings.dry_run:
            result = c.execute(query)

    logger.debug(result)

    return False


def run_aggregates_demand_network(networks: list[NetworkSchema] | None = None) -> None:
    """Run the demand aggregates for each provided network"""

    if not networks:
        networks = [NetworkNEM, NetworkWEM]

    for network in networks:

        if not network.data_first_seen:
            logger.error(f"run_aggregates_demand_network: Network {network.code} has no data_first_seen")
            continue

        exec_aggregates_network_demand_query(date_min=network.data_first_seen, date_max=get_today_nem(), network=network)


def run_aggregates_demand_network_days(days: int = 3) -> None:
    """Run the demand aggregates"""

    date_max = get_today_nem().replace(hour=0, minute=0, second=0, microsecond=0)
    date_min = date_max - timedelta(days=days)

    for network in [NetworkNEM, NetworkWEM]:
        exec_aggregates_network_demand_query(date_min=date_min, date_max=date_max, network=network)  # type: ignore


# Debug entry point
if __name__ == "__main__":
    run_aggregates_demand_network()
