""" OpenNEM output price module



"""
import logging
from datetime import datetime

import pandas as pd

from opennem.api.stats.schema import OpennemDataSet
from opennem.db import get_database_engine
from opennem.queries.price import get_network_region_price_query
from opennem.schema.network import NetworkSchema

logger = logging.getLogger("opennem.controllers.output.price")


class PriceOutputControllerException(Exception):
    pass


def price_per_interval_as_opennem(
    network: NetworkSchema,
    date_min: datetime,
    date_max: datetime | None = None,
    network_region_code: str | None = None,
) -> list[dict]:
    """
    Gets the price for a network region as a list of dicts
    """
    engine = get_database_engine()

    query = get_network_region_price_query(
        network=network, date_min=date_min, date_max=date_max, network_region_code=network_region_code
    )

    return_records = []

    with engine.begin() as conn:
        for record in conn.execute(query):
            return_records.append(dict(record))

    return return_records


def price_per_interval_as_dataframe(
    network: NetworkSchema,
    date_min: datetime,
    date_max: datetime | None = None,
    network_region_code: str | None = None,
) -> OpennemDataSet | None:
    """
    Gets the price for a network or network region as a dataframe
    """

    engine = get_database_engine()

    query = get_network_region_price_query(
        network=network, date_min=date_min, date_max=date_max, network_region_code=network_region_code
    )

    price_result_df = pd.read_sql(query, con=engine, index_col=["trading_interval", "network_id", "network_region"])

    if price_result_df.empty:
        raise PriceOutputControllerException("No results from load_interconnector_intervals")

    # convert index to local timezone
    price_result_df.index.tz_localize(network.get_fixed_offset(), ambiguous="infer")

    return price_result_df


if __name__ == "__main__":
    from opennem.schema.network import NetworkNEM

    interval = datetime.fromisoformat("2023-06-29T10:00:00+10:00")

    r = price_per_interval_as_opennem(
        network=NetworkNEM,
        date_min=interval,
    )

    for i in r:
        print(i)

    df = price_per_interval_as_dataframe(
        network=NetworkNEM,
        date_min=interval,
    )

    print("done")
