#!/usr/bin/env python
""" Crates the OPENNEM ROOFTOP BACKFILL network"""

import logging

from sqlalchemy import text as sql

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.rooftop_backfill")


def run_import_opennem_rooftop_backfill() -> None:
    """Runs the query that creates OPENNEM ROOFTOP BACKFILL"""

    query = sql(
        """
        insert into facility_scada
        (
            created_by,
            created_at,
            network_id,
            trading_interval,
            facility_code,
            generated,
            eoi_quantity,
            is_forecast,
            energy_quality_flag
        )
        select
            'opennem.backfill' as created_by,
            now() as created_at,
            'OPENNEM_ROOFTOP_BACKFILL' as network_id,
            fs.trading_interval as trading_interval,
            facility_code,
            generated,
            generated / 4 as eoi_quantity,
            is_forecast,
            0
        from facility_scada fs
        where
            fs.network_id = 'APVI' and
            fs.trading_interval < '2018-03-01T00:00:00+10:00'
        ;


    """
    )

    engine = get_database_engine()

    with engine.begin() as conn:
        logger.debug(query)
        conn.execute(query)


if __name__ == "__main__":
    run_import_opennem_rooftop_backfill()
