#!/usr/bin/env python
""" Find unmapped DUIDS in scada data and match with MMS and then import.
This is intended as a one-off script but keeping it around for future ref
to automate

@TODO automate adding MMS stations / merging with existing data based on facs
seen from worker/monitor.
"""
import csv
import json
import logging
from pathlib import Path

from opennem.db import SessionLocal
from opennem.db.models.opennem import Station
from opennem.importer.db import mms_init
from opennem.monitors.facility_seen import FacilitySeen, ignored_duids
from opennem.schema.opennem import FacilitySchema, StationSchema
from opennem.schema.stations import StationSet

logger = logging.getLogger("unmapped_duids")


def get_mms() -> StationSet:
    mms_source_file = Path(__file__).parent.parent / "opennem" / "data" / "mms.json"
    mms_json = None

    with mms_source_file.open() as fh:
        mms_json = json.load(fh)

    mms_ss = StationSet()

    [mms_ss.add_dict(i) for i in mms_json]

    return mms_ss


def find_fac_in_mms(code: str, mms: StationSet) -> FacilitySchema | None:
    for station in mms:
        for fac in station.facilities:
            if fac.code == code:
                return fac

    return None


def find_station_in_mms(code: str, mms: StationSet) -> StationSchema | None:
    for station in mms:
        for fac in station.facilities:
            if fac.code == code:
                return station

    return None


def station_is_in_db(station_code: str) -> Station | None:
    session = SessionLocal()

    if station_code in NEM_STATION_REMAP.keys():
        station_code = NEM_STATION_REMAP[station_code]

    station_lookup = session.query(Station).filter_by(code=station_code).all()
    station = None

    if station_lookup:
        station = station_lookup.pop()

    return station


NEM_STATION_REMAP = {"SWANBANK": "SWAN_B", "CALLIDE": "CALL_A"}


def list_unmapped() -> None:
    """Print out and find the umapped DUIDS"""
    unmapped_source = Path(__file__).parent.parent / "data" / "unmapped.csv"

    if not unmapped_source.is_file():
        logger.error(f"File not found: {unmapped_source}")

    recs = []

    with unmapped_source.open() as fh:
        csvreader = csv.reader(fh)
        recs = [FacilitySeen(code=i[0], network_id=i[1]) for i in csvreader]

    recs_filtered = ignored_duids(recs)

    recs_nem = list(filter(lambda x: x.network_id == "NEM", recs_filtered))
    recs_nem = sorted(recs_nem, key=lambda x: x.code)

    mms = get_mms()

    for fac_seen in recs_nem:
        found_fac = find_fac_in_mms(fac_seen.code, mms)

        if found_fac:
            found_station = find_station_in_mms(fac_seen.code, mms)
            station_model = None

            if found_station:
                station_model = station_is_in_db(found_station.code)

            logger.info(
                "For {} found station {} with {} facilities and db : {}".format(
                    fac_seen.code,
                    found_station.code if found_station else "none",
                    len(found_station.facilities) if found_station and found_station.facilities else 0,
                    station_model.code if station_model else "none",
                )
            )
        else:
            logger.info(f"Cound not find facility for {fac_seen.code}")


if __name__ == "__main__":
    mms_init()
    # list_unmapped()
