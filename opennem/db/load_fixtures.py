import json
import os

from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import FuelTech
from opennem.db.models.wem import metadata

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")

engine = db_connect()
session = sessionmaker(bind=engine)


def load_fixture(fixture_name):
    fixture_path = os.path.join(FIXTURE_PATH, f"{fixture_name}.json")

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture


def load_fueltechs():
    fixture = load_fixture("fueltechs")

    s = session()

    for fueltech in fixture:
        ft = FuelTech(**fueltech)
        s.add(ft)

    s.commit()


if __name__ == "__main__":
    load_fueltechs()
