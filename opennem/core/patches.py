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
        "update facility set capacity_registered = 2.0, unit_capacity = 2.0 where code = 'GOSNELLS'",
        "update facility set capacity_registered = 1.1, unit_capacity = 1.1  where code = 'ATLAS'",
        # code GULLRWF2_74 -> Biala
        # "update facility set station_id = null where code = 'GULLRWF2'",
        # "update facility set code = 'GULLRWF2' where name_clean = 'Biala'",
        "update facility set station_id = (select id from station where name = 'Wivenhoe Small Hydro') where code ='WIVENSH'",
        "update station set name_clean = 'Wivenhoe Mini' where name_clean = 'Wivenhoe Small'",
        "update facility set fueltech_id = 'pumps' where code in ('PUMP2', 'PUMP1')",
        "update facility set station_id = null where name='Crookwell' and code is null",
        "update facility set station_id = null where name='Pioneer Sugar Mill' and code is null",
    ]

    with engine.connect() as c:

        for query in sqls:
            rows = c.execute(query)
            pprint(rows)


if __name__ == "__main__":
    patches()
