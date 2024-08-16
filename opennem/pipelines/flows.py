"""OpenNEM flows pipelines


Runs the flows process per-interval as part of flows v2

Will check that all available data is present before running the flow update
"""

import dataclasses
import logging
from datetime import datetime
from itertools import starmap

from sqlalchemy import text as sql

from opennem.aggregates.network_flows import run_flow_update_for_interval
from opennem.db import get_database_engine
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.pipelines.flows")


class OpennemNoFlowData(Exception):
    """Raised when all the compelte data isn't available to calculate flows"""

    pass


@dataclasses.dataclass
class CrawlerHistory:
    interval: int
    crawler_name: str
    inserted_records: int
    processed_time: int


def get_flow_depends_crawler_history() -> list[CrawlerHistory]:
    """Get the crawler history for the last interval

    @TODO support going further back in history
    """
    engine = get_database_engine()

    crawler_history_query = sql(
        """
        select
            ch.interval,
            ch.crawler_name,
            ch.inserted_records,
            ch.processed_time
        from crawl_history ch
        where
            ch.interval = nemweb_latest_interval()
            and ch.network_id = 'NEM'
            and ch.crawler_name in ('au.nemweb.dispatch_scada', 'au.nemweb.dispatch_is');
    """
    )

    with engine.begin() as conn:
        results = conn.execute(crawler_history_query).fetchall()

    result_models = list(starmap(CrawlerHistory, results))

    return result_models


def get_latest_flow_interval_processed() -> datetime:
    """Get the latest interval processed from the flow table"""
    engine = get_database_engine()

    flows_latest_query = sql(
        """
        select
            max(nf.trading_interval)
        from at_network_flows nf
        where
            nf.network_id = 'NEM';
    """
    )

    with engine.begin() as conn:
        latest_interval = conn.execute(flows_latest_query).fetchone()

    logger.info(f"Latest interval processed: {latest_interval}")

    return latest_interval


def per_interval_flows_and_exports(network: NetworkSchema, interval: datetime) -> None:
    """Per interval processor for flows"""
    latest_interval = get_latest_flow_interval_processed()

    run_flow_update_for_interval(interval=latest_interval, network=network)


# debug entry point
if __name__ == "__main__":
    flow_results = get_flow_depends_crawler_history()
    print(flow_results)
    get_latest_flow_interval_processed()
