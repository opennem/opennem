"""
    Script to import BOM observations from large tab-del
    CSV files

"""

import csv
import logging
from pathlib import Path
from typing import Dict

import pytz
from sqlalchemy.dialects.postgresql import insert

from opennem.core.normalizers import is_number
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BomObservation, BomStation
from opennem.pipelines.bom import STATE_TO_TIMEZONE
from opennem.utils.dates import parse_date

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("bom.importer")
logger.setLevel(logging.DEBUG)

LIMIT_REC = 0

BOM_BACKUP_FILE = "bom.data"
BOM_BACKUP_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / Path("infra/backups")
    / Path(BOM_BACKUP_FILE)
)


def load_station_timezone_map() -> Dict:
    s = SessionLocal()
    stations = s.query(BomStation).all()

    station_map = {
        s.code: STATE_TO_TIMEZONE[s.state.upper()] for s in stations
    }

    return station_map


STATION_TIMEZONE_MAP = load_station_timezone_map()


def parse_record(rec: Dict) -> Dict:

    timezone = pytz.timezone(STATION_TIMEZONE_MAP[rec["station_id"]])

    observation_time = parse_date(
        rec["observation_time"], is_utc=True, dayfirst=False
    ).astimezone(timezone)

    return {
        "observation_time": observation_time,
        "station_id": rec["station_id"],
        "temp_apparent": float(rec["temp_apparent"])
        if is_number(rec["temp_apparent"])
        else None,
        "temp_air": float(rec["temp_air"])
        if is_number(rec["temp_air"])
        else None,
        "press_qnh": float(rec["press_qnh"])
        if is_number(rec["press_qnh"])
        else None,
        "wind_dir": rec["wind_dir"],
        "wind_spd": float(rec["wind_spd"])
        if is_number(rec["wind_spd"])
        else None,
        "wind_gust": float(rec["wind_gust"])
        if is_number(rec["wind_gust"])
        else None,
        "humidity": float(rec["humidity"])
        if is_number(rec["humidity"])
        else None,
        "cloud": rec["cloud"],
        "cloud_type": rec["cloud_type"],
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
            records_to_store.append(parse_record(row))

            count_rec += 1
            if LIMIT_REC > 0 and count_rec > LIMIT_REC:
                break

    session = SessionLocal()
    engine = get_database_engine()

    stmt = insert(BomObservation).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["observation_time", "station_id"],
        set_={
            "temp_apparent": stmt.excluded.temp_apparent,
            "temp_air": stmt.excluded.temp_air,
            "press_qnh": stmt.excluded.press_qnh,
            "wind_dir": stmt.excluded.wind_dir,
            "wind_spd": stmt.excluded.wind_spd,
            "wind_gust": stmt.excluded.wind_gust,
            "cloud": stmt.excluded.cloud,
            "cloud_type": stmt.excluded.cloud_type,
            "humidity": stmt.excluded.humidity,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error: {}".format(e))
        return 0
    finally:
        session.close()

    logger.info("Inserted {} records".format(len(records_to_store)))


if __name__ == "__main__":
    main()
