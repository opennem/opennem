"""
OpenNEM Facility Capacities


"""

from textwrap import dedent
from typing import Dict

from opennem.db import get_database_engine
from opennem.schema.network import NetworkSchema


def facility_capacity_network_region_fueltech_query(
    network: NetworkSchema, network_region: str
) -> str:
    query = """
    select
        f.fueltech_id,
        sum(f.capacity_registered)
    from facility f
    where
        f.network_id='{network_id}'
        and f.network_region='{network_region}'
        and f.active is True
    group by 1
    order by 1;
    """.format(
        network_id=network.code, network_region=network_region
    )

    return dedent(query)


def get_facility_capacities(network: NetworkSchema, network_region: str) -> Dict:
    engine = get_database_engine()

    query = facility_capacity_network_region_fueltech_query(
        network=network, network_region=network_region
    )
    results = []

    with engine.connect() as c:
        results = list(c.execute(query))

    return_dict = {i[0]: i[1] for i in results}

    return return_dict
