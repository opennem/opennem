import csv
import json
import os
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.bom import BomStation
from opennem.db.models.opennem import FacilityStatus, FuelTech
from opennem.db.models.wem import metadata

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures")

engine = db_connect()
session = sessionmaker(bind=engine)


def load_fixture(fixture_name):
    fixture_path = os.path.join(FIXTURE_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture


def load_fueltechs():
    fixture = load_fixture("fueltechs.json")

    s = session()

    for fueltech in fixture:
        ft = FuelTech(code=fueltech)

        try:
            s.add(ft)
            s.commit()
        except Exception:
            print("Have {}".format(ft.code))


def load_facilitystatus():
    fixture = load_fixture("facility_status.json")

    s = session()

    for status in fixture:
        ft = FacilityStatus(code=status["code"], label=status["label"])

        try:
            s.add(ft)
            s.commit()
        except Exception:
            print("Have {}".format(ft.code))


def parse_date(date_str):
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.date()


def parse_fixed_line(line):
    return (
        str(line[:6]),
        str(line[8:11]).strip(),
        str(line[18:59]).strip(),
        parse_date(line[59:67]),
        Decimal(line[75:83]),
        Decimal(line[84:]),
    )


def load_bom_stations():
    s = session()

    with open(os.path.join(FIXTURE_PATH, "stations_db.txt")) as fh:
        lines = fh.readlines()
        for line in lines:
            code, state, name, registered, lat, lng = parse_fixed_line(line)
            station = BomStation(
                code=code,
                state=state,
                name=name,
                registered=registered,
                lat=lat,
                lng=lng,
            )

            try:
                s.add(station)
                s.commit()
            except Exception:
                print("Have {}".format(station.code))


if __name__ == "__main__":
    load_fueltechs()
    load_facilitystatus()
    load_bom_stations()
