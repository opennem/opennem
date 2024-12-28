"""Runs queries to populate the aggregate tables with facility data

This populated the at_network_demand aggregate table with demand data.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import TextClause, text

from opennem import settings
from opennem.db import get_database_engine
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import get_last_completed_interval_for_network, get_today_nem

logger = logging.getLogger("opennem.aggregates.demand")


class AggregateDemandException(Exception):
    """Exception that is raised when there is an error in the demand aggregate"""

    pass


def aggregates_network_demand_query(date_max: datetime, date_min: datetime, network: NetworkSchema) -> TextClause:
    """This query updates the aggregate demand table with market_value and energy"""

    __query = """
    insert into at_network_demand
        select
            time_bucket('1 day', fs.interval) as trading_day,
            fs.network_id,
            fs.network_region,
            sum(fs.demand_energy) / 1000 as demand_energy,
            sum(fs.demand_market_value) as demand_market_value
        from (
            select
                time_bucket_gapfill('5 minutes', bs.interval) as interval,
                bs.network_id,
                bs.network_region,
                locf(sum(bs.demand) / 12)  as demand_energy,
                locf(max(bs.price) * sum(bs.demand) / 12) as demand_market_value
            from mv_balancing_summary bs
            where
                bs.interval between '{date_min}' and '{date_max}'
                and network_id in ('{network_code}')
            group by 1, 2, 3
        ) as fs
        group by
            1, 2, 3
    on conflict (trading_day, network_id, network_region) DO UPDATE set
            demand_energy = EXCLUDED.demand_energy,
            demand_market_value = EXCLUDED.demand_market_value;
    """

    if date_max <= date_min:
        raise AggregateDemandException(
            f"aggregates_network_demand_query: date_max ({date_max}) is before or equal to date_min ({date_min})"
        )

    query = __query.format(
        date_min=date_min,
        date_max=date_max,
        network_code=network.code,
    )

    return text(query)


async def exec_aggregates_network_demand_query(date_min: datetime, date_max: datetime, network: NetworkSchema) -> bool:
    engine = get_database_engine()

    if date_max < date_min:
        raise AggregateDemandException(
            f"exec_aggregates_network_demand_query: date_max ({date_max}) is prior to date_min ({date_min})"
        )

    query = aggregates_network_demand_query(date_min=date_min, date_max=date_max, network=network)

    async with engine.begin() as conn:
        logger.debug(query)

        if not settings.dry_run:
            await conn.execute(query)

    return False


async def run_aggregates_demand_network(networks: list[NetworkSchema] | None = None) -> None:
    """Run the demand aggregates for each provided network

    @NOTE This runs for the entier range
    """

    if not networks:
        networks = [NetworkNEM, NetworkWEM]

    for network in networks:
        if not network.data_first_seen:
            logger.error(f"run_aggregates_demand_network: Network {network.code} has no data_first_seen")
            continue

        date_min = network.data_first_seen.replace(tzinfo=None, microsecond=0)
        date_max = get_today_nem().replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)

        await exec_aggregates_network_demand_query(date_min=date_min, date_max=date_max, network=network)


async def run_aggregates_demand_network_days(days: int = 3) -> None:
    """Run the demand aggregates"""

    date_max = get_today_nem().replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
    date_min = date_max - timedelta(days=days)

    for network in [NetworkNEM, NetworkWEM]:
        await exec_aggregates_network_demand_query(date_min=date_min, date_max=date_max, network=network)  # type: ignore


async def run_aggregates_demand_for_interval(
    interval: datetime, network: NetworkSchema | None = None, offset: int = 1
) -> int | None:
    """Runs and stores emission flows for a particular interval"""

    if not network:
        network = NetworkNEM

    date_end = interval
    date_start = interval.replace(hour=0, minute=0, second=0, microsecond=0)

    return await exec_aggregates_network_demand_query(date_min=date_start, date_max=date_end, network=network)


async def run_demand_aggregates_for_latest_interval(network: NetworkSchema) -> None:
    """Runs facility aggregates for the latest interval"""
    interval = get_last_completed_interval_for_network(network=network)

    if not interval:
        raise Exception("No latest interval found")

    await run_aggregates_demand_for_interval(interval=interval, network=network)


# Debug entry point
if __name__ == "__main__":
    import asyncio

    asyncio.run(run_aggregates_demand_network_days(days=32))
