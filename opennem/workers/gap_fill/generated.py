"""OpenNEM Gapfill for all intervals
"""

import enum
import logging
from datetime import datetime
from textwrap import dedent

from opennem.clients.slack import slack_message
from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkSchema, NetworkWEM
from opennem.settings import settings

logger = logging.getLogger("opennem.workers.gap_fill")


class GeneratedGap(BaseConfig):
    interval: datetime
    network_id: str
    has_power: bool
    total_generated: float | None


class GapfillType(enum.Enum):
    generated = "generated"
    rooftop = "rooftop"
    flows = "flows"


def query_generated_gaps(
    network: NetworkSchema = NetworkNEM, days: int = 7, gap_type: GapfillType = GapfillType.generated
) -> list[GeneratedGap]:
    """Check for data gaps"""
    engine = get_database_engine()

    query = """

        select
            t.interval at time zone '{tz}' as interval,
            t.network_id,
            t.has_power,
            t.total_generated
        from (
            select
                time_bucket_gapfill('{interval_size} min', fs.trading_interval ) as interval,
                fs.network_id,
                case when sum(fs.generated) is NULL then FALSE else TRUE end as has_power,
                sum(fs.generated) as total_generated
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            where
                fs.trading_interval >= now() - interval '{days} days 2 hours'
                and fs.trading_interval < now() - interval '2 hours'
                and fs.network_id='{network_id}'
                {gapfill_type_filter}
            group by 1, fs.network_id
        ) as t
        where
            t.has_power is FALSE
            order by t.interval desc;

    """

    _results = []

    gapfill_type_filter = ""

    if gap_type == GapfillType.generated:
        gapfill_type_filter = "and f.fueltech_id not in ('imports', 'exports', 'solar_rooftop')"
    elif gap_type == GapfillType.rooftop:
        gapfill_type_filter = "and f.fueltech_id in ('solar_rooftop')"
    elif gap_type == GapfillType.flows:
        gapfill_type_filter = "and f.fueltech_id in ('imports', 'exports')"
    else:
        raise Exception(f"Invalid gap fill type: {gap_type}")

    # for case of WEM and rooftop check the APVI network
    if network == NetworkWEM and gap_type == GapfillType.rooftop:
        network = NetworkAPVI

    _query = query.format(
        tz=network.timezone_database,
        network_id=network.code,
        days=days,
        interval_size=network.interval_size,
        gapfill_type_filter=gapfill_type_filter,
    )

    logger.debug(dedent(_query))

    with engine.connect() as c:
        _results = c.execute(_query)

    _result_models = [GeneratedGap(**i) for i in _results]

    return _result_models


def run_generated_gapfill_for_network(
    gap_type: GapfillType,
    network: NetworkSchema = NetworkNEM,
    days: int = 7,
) -> list[GeneratedGap]:
    """Find gaps for network and gap type"""
    generated_gaps = query_generated_gaps(network, days=days, gap_type=gap_type)

    logger.info(f"Found {len(generated_gaps)} generated gaps")

    for gap in generated_gaps:
        logger.info(f"{gap.network_id} Running for interval {gap.interval} with power: {gap.has_power}")

        if settings.dry_run:
            continue

    return generated_gaps


def check_generated_gaps(days: int = 3) -> None:
    """Process for checking how many generation gaps there might be"""

    for network in [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop]:
        for _, gap_type in enumerate(GapfillType):
            gaps = run_generated_gapfill_for_network(days=days, network=network, gap_type=gap_type)

            if gaps:
                slack_message(f"Found {len(gaps)} generation gaps in {network.code} for {gap_type} @nik")
                logger.error(f"Found {len(gaps)} generation gaps in {network.code} for {gap_type}")


# debug entry point
if __name__ == "__main__":
    check_generated_gaps(days=30)
    # run_generated_gapfill_for_network(days=365)
