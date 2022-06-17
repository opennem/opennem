""" Updates the network items in the database with the data ranges


"""
import logging
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import text as sql

from opennem.db import get_database_engine, get_scoped_session
from opennem.db.models.opennem import Network

logger = logging.getLogger("opennem.workers.network_data_range")


@dataclass
class NetworkDataDateRanges:
    network: str
    data_min: datetime
    data_max: datetime | None


def get_network_data_ranges() -> list[NetworkDataDateRanges]:
    """Runs a query to get the network data ranges"""
    engine = get_database_engine()

    stmt = sql(
        """
        select
            fs.network_id,
            min(fs.trading_interval) as scada_min,
            max(fs.trading_interval) as scada_max
        from facility_scada fs
        where
            fs.is_forecast is FALSE
        group by fs.network_id;
    """
    )

    with engine.connect() as c:
        results = list(c.execute(stmt))

    if not results:
        raise Exception("No results for data range query in update_network_data_ranges")

    models = [NetworkDataDateRanges(network=i[0], data_min=i[1], data_max=i[2]) for i in results]

    return models


def update_network_data_ranges(data_ranges: list[NetworkDataDateRanges]) -> None:
    """Updates the data ranges in the network"""

    with get_scoped_session() as sess:
        for date_range in data_ranges:
            network = sess.query(Network).get(date_range.network)

            if not network:
                raise Exception(f"Could not find network {date_range.network}")

            network.data_start_date = date_range.data_min
            network.data_end_date = date_range.data_max

            sess.add(network)

        sess.commit()


def run_network_data_range_update() -> None:
    """Runs the network data range update"""
    data_ranges = get_network_data_ranges()
    update_network_data_ranges(data_ranges)


if __name__ == "__main__":
    run_network_data_range_update()
