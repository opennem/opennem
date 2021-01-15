#!/usr/bin/env python
"""
Script to run + export a query against the database

"""
import csv
import logging
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional

from opennem.api.export.controllers import gov_stats_cpi, power_flows_week
from opennem.api.export.queries import interconnector_flow_power_query
from opennem.api.stats.controllers import get_scada_range
from opennem.api.stats.schema import RegionFlowResult
from opennem.core.flows import net_flows
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


def get_test_fixture() -> List[Dict]:
    csv_fixture = Path(__file__).parent.parent / "tests/fixtures/test_interconnector_sa1.csv"

    if not csv_fixture.is_file():
        raise Exception("not a file")

    records = []

    with csv_fixture.open() as fh:
        csvreader = csv.DictReader(fh)

        for r in csvreader:
            records.append(r)

    return records


def run_query_inter() -> Optional[StringIO]:
    # engine = get_database_engine()

    # results = []
    # scada_range = get_scada_range(network=NetworkNEM, network_region="VIC1")

    # s = power_flows_week(network=NetworkNEM, network_region_code="VIC1", date_range=scada_range)

    # if not s:
    #     return None
    records = get_test_fixture()

    stats: List[RegionFlowResult] = [
        RegionFlowResult(
            interval=i["trading_interval"],
            generated=i["facility_power"],
            flow_from=i["flow_from"],
            flow_to=i["flow_to"] if len(i) > 1 else None,
        )
        for i in records
    ]

    stats_grouped = net_flows("SA1", stats)

    imports = stats_grouped["imports"]
    exports = stats_grouped["exports"]

    from pprint import pprint

    pprint(imports)
    print("\nexports\n")
    pprint(exports)

    return None
    # return s.json(indent=4)


def run_query():
    s = gov_stats_cpi()

    print(s)


if __name__ == "__main__":
    r = run_query_inter()
    print(r)
