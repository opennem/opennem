"""OpenNEM Gapfill for all intervals
"""

import enum
import logging
from datetime import datetime
from textwrap import dedent

from opennem import settings
from opennem.db import get_database_engine
from opennem.notifications.slack import slack_message
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM, NetworkSchema

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

    match gap_type:
        case GapfillType.generated:
            gapfill_type_filter = "and f.fueltech_id not in ('imports', 'exports', 'solar_rooftop')"
        case GapfillType.rooftop:
            gapfill_type_filter = "and f.fueltech_id in ('solar_rooftop')"
        case GapfillType.flows:
            gapfill_type_filter = "and f.fueltech_id in ('imports', 'exports')"
        case _:
            raise Exception(f"Invalid gap fill type: {gap_type}")

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


def run_generated_gapfill_for_network(network: NetworkSchema = NetworkNEM, days: int = 7) -> list[GeneratedGap]:
    generated_gaps = query_generated_gaps(network, days=days)

    logger.info("Found {} generated gaps".format(len(generated_gaps)))

    for gap in generated_gaps:
        logger.info("{} Running for interval {} with power: {}".format(gap.network_id, gap.interval, gap.has_power))

        if settings.dry_run:
            continue

    return generated_gaps


def check_generated_gaps() -> None:
    """Process for checking how many generation gaps there might be"""
    gaps = run_generated_gapfill_for_network(days=3)

    if gaps:
        slack_message(f"Found {len(gaps)} generation gaps @nik")


# debug entry point
if __name__ == "__main__":
    run_generated_gapfill_for_network(days=365)
