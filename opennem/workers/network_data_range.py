""" Updates the network items in the database with the data ranges


"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import text as sql

from opennem.core.profiler import profile_task
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import Network
from opennem.utils.dates import get_today_nem

logger = logging.getLogger("opennem.workers.network_data_range")


@dataclass
class NetworkDataDateRanges:
    network: str
    data_min: datetime | None
    data_max: datetime | None


def get_network_data_ranges(query_min: bool = False, days_back: int = 7) -> list[NetworkDataDateRanges]:
    """Runs a query to get the network data ranges"""
    engine = get_database_engine()

    date_min: datetime = get_today_nem() - timedelta(days=days_back)

    stmt = sql(
        """
            select
                fs.network_id,
                null as scada_min,
                max(fs.trading_interval) as scada_max
            from facility_scada fs
            where
                fs.is_forecast is FALSE and
                fs.trading_interval > :date_min
            group by fs.network_id;
        """
    )

    if query_min:
        stmt = sql(
            """
            select
                fs.network_id,
                min(f.data_first_seen) as scada_min,
                max(fs.trading_interval) as scada_max
            from facility_scada fs
            left join facility f on fs.facility_code = f.code
            where
                fs.is_forecast is FALSE and
                fs.trading_interval > :date_min
            group by fs.network_id;
        """
        )

    with engine.begin() as c:
        logger.debug(stmt)
        results = list(c.execute(stmt, {"date_min": date_min}))

    if not results:
        raise Exception("No results for data range query in update_network_data_ranges")

    models = [NetworkDataDateRanges(network=i[0], data_min=i[1], data_max=i[2]) for i in results]

    return models


def update_network_data_ranges(data_ranges: list[NetworkDataDateRanges]) -> None:
    """Updates the data ranges in the network"""

    with SessionLocal() as sess:
        for date_range in data_ranges:
            network = sess.get(Network, date_range.network)

            if not network:
                raise Exception(f"Could not find network {date_range.network}")

            if date_range.data_min:
                network.data_start_date = date_range.data_min

            if date_range.data_max:
                network.data_end_date = date_range.data_max

            sess.add(network)

        sess.commit()


@profile_task(send_slack=False)
def run_network_data_range_update(debug: bool = False) -> None:
    """Runs the network data range update"""
    data_ranges = get_network_data_ranges()

    if debug:
        for data_range in data_ranges:
            logger.debug(f"{data_range.network} {data_range.data_min} {data_range.data_max}")

    update_network_data_ranges(data_ranges)


if __name__ == "__main__":
    run_network_data_range_update(debug=True)
