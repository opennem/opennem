#!/usr/bin/env python
"""
    Script to import BOM observations from large tab-del
    CSV files

"""

import csv
import logging
import sys
from pathlib import Path
from typing import Dict

import pytz
from pydantic.types import FilePath

from opennem.core.normalizers import is_number
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BomObservation, BomStation
from opennem.pipelines.bom import STATE_TO_TIMEZONE
from opennem.pipelines.bulk_insert import build_insert_query
from opennem.pipelines.csv import generate_csv_from_records
from opennem.utils.dates import parse_date

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("bom.importer")
logger.setLevel(logging.DEBUG)

LIMIT_REC = 0

BOM_BACKUP_FILE = "bom.data"
BOM_BACKUP_PATH = (
    Path(__file__).resolve().parent.parent.parent / Path("infra/backups") / Path(BOM_BACKUP_FILE)
)


def load_station_timezone_map() -> Dict:
    s = SessionLocal()
    stations = s.query(BomStation).all()

    station_map = {s.code: STATE_TO_TIMEZONE[s.state.upper()] for s in stations}

    return station_map


STATION_TIMEZONE_MAP = load_station_timezone_map()


def parse_record(rec: Dict) -> Dict:
    """Parse BoM records in database format"""

    timezone = pytz.timezone(STATION_TIMEZONE_MAP[rec["station_id"]])

    observation_time = parse_date(rec["observation_time"], is_utc=True, dayfirst=False).astimezone(
        timezone
    )

    return {
        "observation_time": observation_time,
        "station_id": rec["station_id"],
        "temp_apparent": float(rec["temp_apparent"]) if is_number(rec["temp_apparent"]) else None,
        "temp_air": float(rec["temp_air"]) if is_number(rec["temp_air"]) else None,
        "press_qnh": float(rec["press_qnh"]) if is_number(rec["press_qnh"]) else None,
        "wind_dir": rec["wind_dir"],
        "wind_spd": float(rec["wind_spd"]) if is_number(rec["wind_spd"]) else None,
        "cloud": rec["cloud"],
        "cloud_type": rec["cloud_type"],
        "humidity": float(rec["humidity"]) if is_number(rec["humidity"]) else None,
        "wind_gust": float(rec["wind_gust"]) if is_number(rec["wind_gust"]) else None,
    }


def parse_record_bom(rec: Dict) -> Dict:
    """Parse CSV records in BOM format"""

    timezone = pytz.timezone(STATION_TIMEZONE_MAP[rec["station_id"]])

    observation_time = parse_date(rec["observation_time"], is_utc=True, dayfirst=False).astimezone(
        timezone
    )

    return {
        "observation_time": observation_time,
        "station_id": rec["station_id"],
        "temp_apparent": float(rec["temp_apparent"].strip())
        if is_number(rec["temp_apparent"])
        else None,
        "temp_air": float(rec["temp_air"].strip()) if is_number(rec["temp_air"]) else None,
        "press_qnh": None,
        "wind_dir": None,
        "wind_spd": None,
        "cloud": None,
        "cloud_type": None,
        "humidity": float(rec["humidity"].strip()) if is_number(rec["humidity"]) else None,
        "wind_gust": None,
    }


def main():
    if not BOM_BACKUP_PATH.is_file():
        raise Exception("Not a file: {}".format(BOM_BACKUP_PATH))

    fieldnames = [i.name for i in BomObservation.__table__.columns.values()]

    records_to_store = []

    with BOM_BACKUP_PATH.open() as fh:
        csvreader = csv.DictReader(fh, fieldnames=fieldnames, delimiter="\t")

        count_rec = 0

        for row in csvreader:
            parsed_row = parse_record(row)
            records_to_store.append(parsed_row)

            count_rec += 1
            if LIMIT_REC > 0 and count_rec > LIMIT_REC:
                break

    update_fields = [
        "temp_apparent",
        "temp_air",
        "press_qnh",
        "wind_dir",
        "wind_spd",
        "wind_gust",
        "cloud",
        "cloud_type",
        "humidity",
    ]

    sql_query = build_insert_query(BomObservation, update_fields)

    conn = get_database_engine().raw_connection()
    cursor = conn.cursor()
    csv_content = generate_csv_from_records(
        BomObservation,
        records_to_store,
        column_names=records_to_store[0].keys(),
    )

    cursor.copy_expert(sql_query, csv_content)
    conn.commit()

    logger.info("Inserted {} records".format(len(records_to_store)))


BOM_FORMAT_FIELDS = [
    "hm",
    "station_id",
    "station_name",
    "observation_time",
    "temp_air",
    "Quality of air temperature",
    "temp_apparent",
    "Quality of Wet bulb temperature",
    "Dew point temperature in degrees C",
    "Quality of dew point temperature",
    "Relative humidity in percentage %",
    "Quality of relative humidity",
    "humidity",
    "Quality of vapour pressure",
    "Saturated vapour pressure in hPa",
    "Quality of saturated vapour pressure",
    "AWS Flag",
    "#",
]


BOM_DB_UPDATE_FIELDS = [
    "station_id",
    "observation_time",
    "temp_air",
    "temp_apparent",
    "humidity",
]

DELIMITER = chr(255)

import re

__bom_date_match = re.compile(r"(\d{4})\,(\d{2}),(\d{2}),(\d{2}),(\d{2})")


def bom_pad_stationid(station_id: str) -> str:
    station_id = station_id.strip()

    if len(station_id) == 5:
        station_id = f"0{station_id}"

    return station_id


def bom_parse_date(line: str) -> str:
    """BoM has the worst. date. format. ever."""
    return re.sub(__bom_date_match, r"\1-\2-\3 \4:\5:00", line)


def parse_bom(file: FilePath) -> int:
    num_inserts = 0
    limit = 0
    read_count = 0
    records_to_store = []
    observation_times = []

    with file.open() as fh:
        fh.readline()

        csvreader = csv.DictReader(
            [bom_parse_date(l) for l in fh],
            delimiter=",",
            fieldnames=BOM_FORMAT_FIELDS,
        )
        for row in csvreader:

            row["station_id"] = bom_pad_stationid(row["station_id"])

            record = parse_record_bom(row)

            ot = record["observation_time"]

            if ot in observation_times:
                continue

            observation_times.append(ot)

            records_to_store.append(record)
            read_count += 1

            if limit and limit > 0 and read_count >= limit:
                break

    sql_query = build_insert_query(BomObservation, BOM_DB_UPDATE_FIELDS)

    conn = get_database_engine().raw_connection()
    cursor = conn.cursor()
    csv_content = generate_csv_from_records(
        BomObservation,
        records_to_store,
        column_names=records_to_store[0].keys(),
    )

    cursor.copy_expert(sql_query, csv_content)
    conn.commit()

    return num_inserts


def cli(files) -> None:
    for f in files:
        fp = Path(f)

        if not fp.is_file():
            raise Exception("Bad file: {}".format(fp))

        print("Parsing: {}".format(fp))

        parse_bom(fp)


if __name__ == "__main__":
    cli(sys.argv[1:])
