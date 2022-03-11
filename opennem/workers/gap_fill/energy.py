"""OpenNEM Gapfill
"""

import logging
from datetime import datetime, timedelta
from textwrap import dedent
from typing import List, Optional

from opennem import settings
from opennem.core.networks import network_from_network_code
from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig
from opennem.schema.network import (
    NetworkAEMORooftop,
    NetworkAPVI,
    NetworkNEM,
    NetworkSchema,
    NetworkWEM,
)
from opennem.workers.energy import run_energy_calc

logger = logging.getLogger("opennem.workers.gap_fill")


class EnergyGap(BaseConfig):
    interval: datetime
    network_id: str
    has_power: bool
    has_energy: bool
    total_generated: Optional[float]
    total_energy: Optional[float]


def query_energy_gaps(network: NetworkSchema = NetworkNEM, days: int = 7) -> List[EnergyGap]:
    engine = get_database_engine()

    query = """

        select
            t.interval at time zone '{tz}' as interval,
            t.network_id,
            t.has_power,
            t.has_energy,
            t.total_generated,
            t.total_energy
        from (
            select
                time_bucket_gapfill('1 hour', fs.trading_interval ) as interval,
                fs.network_id,
                case when sum(fs.generated) is NULL then FALSE else TRUE end as has_power,
                case when sum(fs.eoi_quantity) IS NULL then FALSE else TRUE end as has_energy,
                sum(fs.generated) as total_generated,
                sum(fs.eoi_quantity) as total_energy
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            where
                fs.trading_interval >= now() - interval '{days} days 1 hour'
                and fs.trading_interval < now() - interval '1 hour'
                and fs.network_id='{network_id}'
            group by 1, fs.network_id
        ) as t
        where
            t.has_power is TRUE
            order by t.interval desc;

    """

    _results = []

    _query = query.format(tz=network.timezone_database, network_id=network.code, days=days)

    logger.debug(dedent(_query))

    with engine.connect() as c:
        _results = c.execute(_query)

    _result_models = [EnergyGap(**i) for i in _results]

    return _result_models


def run_energy_gapfill_for_network(
    network: NetworkSchema = NetworkNEM, days: int = 7, run_all: bool = False
) -> None:
    energy_gaps = query_energy_gaps(network, days=days)

    energy_gaps_filtered = list(
        filter(lambda x: x.has_power is True and x.has_energy is False, energy_gaps)
    )

    if run_all:
        energy_gaps_filtered = energy_gaps

    logger.info("Found {} energy gaps interval hours".format(len(energy_gaps_filtered)))

    for gap in energy_gaps_filtered:
        logger.info(
            "{} Running for interval {} with power: {} energy: {} energy_value: {}".format(
                gap.network_id, gap.interval, gap.has_power, gap.has_energy, gap.total_energy
            )
        )

        if settings.dry_run:
            continue

        dmin = gap.interval
        dmax = dmin + timedelta(hours=1)

        try:
            run_energy_calc(dmin, dmax, network=network_from_network_code(gap.network_id))
        except Exception:
            logger.error(
                "Error running {} energy gapfill for {} => {}".format(gap.network_id, dmin, dmax)
            )


def run_energy_gapfill(
    days: int = 14,
    networks: List[NetworkSchema] = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop],
    run_all: bool = False,
) -> None:
    """Run gapfill of energy values - will find gaps in energy values and run energy_sum"""
    for network in networks:
        logger.info("Running energy gapfill for {}".format(network.code))

        try:
            run_energy_gapfill_for_network(network, days=days, run_all=run_all)
        except Exception as e:
            logger.error("gap_fill run error: {}".format(e))


# debug entry point
if __name__ == "__main__":
    run_energy_gapfill()
