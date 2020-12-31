#!/usr/bin/env python
"""
Script to run + export a query against the database

"""
import csv
import logging
from io import StringIO
from typing import Optional

from opennem.api.export.controllers import power_flows_week
from opennem.api.export.queries import interconnector_flow_power_query
from opennem.api.stats.controllers import get_scada_range
from opennem.db import get_database_engine
from opennem.schema.network import NetworkNEM
from opennem.settings import settings

logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger("opennem.run_query")

import psycopg2

QUERY = """
    select
        f.code,
        f.network_name,
        f.fueltech_id,
        f.emissions_factor_co2
    from facility f
    where
        f.code in (select distinct fs.facility_code from facility_scada fs) and
        f.emissions_factor_co2 is null;
"""

QUERY = """
    select code, network_name, fueltech_id, emissions_factor_co2 from facility where fueltech_id in ('coal_black', 'coal_brown') and emissions_factor_co2 is null
"""


def run_query() -> Optional[StringIO]:
    engine = get_database_engine()

    results = []
    scada_range = get_scada_range(network=NetworkNEM, network_region="VIC1")

    s = power_flows_week(
        network=NetworkNEM, network_region_code="VIC1", date_range=scada_range
    )

    if not s:
        return None

    return s.json(indent=4)


if __name__ == "__main__":
    r = run_query()
    print(r)
