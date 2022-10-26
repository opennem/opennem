""" Flow controllers """
from datetime import datetime


from opennem.db import get_database_engine
from opennem.queries.flows import get_interconnector_intervals_query
from opennem.schema.network import NetworkSchema


def get_network_interconnector_intervals(
    date_start: datetime, date_end: datetime, network: NetworkSchema, as_dataframe: bool = False
) -> list[dict]:
    """Get interconnector intervals for a network"""
    engine = get_database_engine()

    query = get_interconnector_intervals_query(date_start, date_end, network)

    with engine.connect() as conn:
        results = conn.execute(query)

    return results
