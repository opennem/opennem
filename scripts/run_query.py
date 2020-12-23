#!/usr/bin/env python
"""
Script to run + export a query against the database

"""
import csv
import logging
from io import StringIO

from opennem.db import get_database_engine

logger = logging.getLogger("opennem.run_query")

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


def run_query() -> StringIO:
    engine = get_database_engine()

    results = []
    csvbuffer = StringIO()

    with engine.connect() as c:
        results = list(c.execute(QUERY))

    csvwriter = csv.writer(csvbuffer)

    for record in results:
        csvwriter.writerow(record)

    # rewind it back to the start
    csvbuffer.seek(0)

    return csvbuffer


if __name__ == "__main__":
    r = run_query()
    print(r.getvalue())
