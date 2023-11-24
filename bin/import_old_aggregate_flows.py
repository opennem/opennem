#!/usr/bin/env python
""" OpenNEM script to import old aggregate flows """


import logging

from sqlalchemy import text as sql

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.old_aggregate_flows")


def import_old_flows_query() -> None:
    """import flow gap"""

    query = sql(
        """
    insert into at_network_flows (
        trading_interval,
        network_id,
        network_region,
        energy_imports,
        energy_exports,
        market_value_imports,
        market_value_exports,
        created_by
    )
    select
        fl.trading_interval,
        fl.network_id,
        fl.network_region,
        fl.imports_energy * 1000 as energy_imports,
        fl.exports_energy * 1000 as energy_exports,
        fl.imports_energy * 1000 * t.price as market_value_imports,
        fl.exports_energy * 1000 * t.price as market_value_exports,
        'opennem.migration.flows' as created_by
    from mv_interchange_energy_nem_region fl
    left join
        (
            select
                time_bucket('1h', bs.trading_interval) as trading_interval,
                bs.network_id,
                bs.network_region,
                avg(bs.price) as price
            from balancing_summary bs
            group by 1,2,3
        ) t on
            fl.trading_interval = t.trading_interval and
            fl.network_id = t.network_id and
            fl.network_region = t.network_region
    where
        fl.trading_interval < '2009-07-01T00:00:00+10:00'
        and fl.trading_interval >= '2009-01-01T00:00:00+10:00'
    on conflict (trading_interval, network_id, network_region)
    do
        update set
            energy_imports = EXCLUDED.energy_imports,
            energy_exports = EXCLUDED.energy_exports,
            market_value_imports = EXCLUDED.market_value_imports,
            market_value_exports = EXCLUDED.market_value_exports,
            created_by = EXCLUDED.created_by;
    """
    )

    engine = get_database_engine()

    with engine.begin() as conn:
        logger.debug(query)
        conn.execute(query)


if __name__ == "__main__":
    import_old_flows_query()
