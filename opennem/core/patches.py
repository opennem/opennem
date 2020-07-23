# GULLRWF2 -> Biala
import json
from datetime import date, datetime
from pprint import pprint

from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import metadata

engine = db_connect()
session = sessionmaker(bind=engine)


def patches():

    sqls = [
        "update wem_facility set capacity_maximum = 2.0 where code = 'GOSNELLS'",
        "update wem_facility set capacity_maximum = 1.1 where code = 'ATLAS'",
        "update nem_facility set station_id = null where code = 'GULLRWF2'",
        "update nem_facility set code = 'GULLRWF2' where name_clean = 'Biala'",
        "update nem_facility set station_id = (select id from nem_station where name = 'Wivenhoe Small Hydro') where code ='WIVENSH'",
        "update nem_station set name_clean = 'Wivenhoe Mini' where name_clean = 'Wivenhoe Small'",
        "update nem_facility set fueltech_id = 'pumps' where code in ('PUMP2', 'PUMP1')",
        "update nem_facility set station_id = null where name='Crookwell' and code is null",
        "update nem_facility set station_id = null where name='Pioneer Sugar Mill' and code is null",
    ]

    with engine.connect() as c:

        for query in sqls:
            rows = c.execute(query)
            pprint(rows)


if __name__ == "__main__":
    patches()
