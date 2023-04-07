"""OpenNEM Network Flows v3

Creates an aggregate table with network flows (imports/exports), emissions
and market_value

"""

# from opennem.db import get_database_engine
# from opennem.db.bulk_insert_csv import build_insert_query, generate_csv_from_records
# from opennem.db.models.opennem import AggregateNetworkFlows
# from opennem.queries.flows import get_interconnector_intervals_query
# from opennem.schema.network import NetworkNEM, NetworkSchema
# from opennem import settings
# from datetime import datetime, timedelta
# from opennem.utils.dates import get_last_complete_day_for_network, get_last_completed_interval_for_network, is_aware
import logging
from datetime import datetime

import pandas as pd

from opennem.db import get_database_engine
from opennem.queries.flows import get_interconnector_intervals_query
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import is_aware

logger = logging.getLogger("opennem.aggregates.flows_v3")


class FlowWorkerException(Exception):
    pass


def load_interconnector_intervals(date_start: datetime, date_end: datetime, network: NetworkSchema | None = None) -> pd.DataFrame:
    """Load interconnector flows for a date range"""
    engine = get_database_engine()

    # default to NEM
    if not network:
        network = NetworkNEM

    if date_start >= date_end:
        raise FlowWorkerException("load_interconnector_intervals: date_start is more recent than date_end")

    query = get_interconnector_intervals_query(date_start=date_start, date_end=date_end, network=network)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    return df_gen


def load_energy_emission_mv_intervals(date_start: datetime, date_end: datetime, network: NetworkSchema) -> pd.DataFrame:
    """Fetch all emission, market value and emission intervals by network region"""

    engine = get_database_engine()

    if not is_aware(date_start):
        date_start = date_start.astimezone(tz=network.get_fixed_offset())

    if not is_aware(date_end):
        date_end = date_end.astimezone(tz=network.get_fixed_offset())

    query = """
        select
            t.trading_interval,
            t.network_region,
            sum(t.power) as generated,
            sum(t.market_value) as market_value,
            sum(t.emissions) as emissions
        from
        (
            select
                fs.trading_interval as trading_interval,
                f.network_region as network_region,
                sum(fs.generated) as power,
                coalesce(sum(fs.generated) * max(bsn.price), 0) as market_value,
                coalesce(sum(fs.generated) * max(f.emissions_factor_co2), 0) as emissions
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            left join network n on f.network_id = n.code
            left join (
                select
                    bs.trading_interval as trading_interval,
                    bs.network_id,
                    bs.network_region,
                    bs.price as price
                from balancing_summary bs
                    where bs.network_id='{network_id}'
            ) as  bsn on
                bsn.trading_interval = fs.trading_interval
                and bsn.network_id = n.network_price
                and bsn.network_region = f.network_region
                and f.network_id = '{network_id}'
            where
                fs.is_forecast is False and
                f.interconnector = False and
                f.network_id = '{network_id}' and
                fs.generated > 0
            group by
                1, f.code, 2
        ) as t
        where
            t.trading_interval >= '{date_start}' and
            t.trading_interval < '{date_end}'
        group by 1, 2
        order by 1 asc, 2;
    """.format(
        date_start=date_start, date_end=date_end, network_id=network.code
    )

    logger.debug(query)

    df_gen = pd.read_sql(query, con=engine, index_col=["trading_interval"])

    if df_gen.empty:
        raise FlowWorkerException("No results from load_interconnector_intervals")

    df_gen.index = df_gen.index.tz_convert(tz=network.get_fixed_offset())

    df_gen["price"] = df_gen["market_value"] / df_gen["generated"]
    df_gen["emission_factor"] = df_gen["emissions"] / df_gen["generated"]

    return df_gen


if __name__ == "__main__":
    pass
