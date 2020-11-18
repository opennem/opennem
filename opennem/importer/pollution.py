import csv
import logging

from opennem.core.normalizers import station_name_cleaner
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Station
from opennem.importer.mms import mms_import
from opennem.utils.http import http
from opennem.utils.mime import decode_bytes

CER_CSV = "http://www.cleanenergyregulator.gov.au/DocumentAssets/Documents/Greenhouse%20and%20energy%20information%20for%20designated%20generation%20facilities%202018-19%20.csv"

logger = logging.getLogger(__name__)


def import_pollution_mms():
    mms = mms_import()

    facility_poll_map = {
        "CALL_A_4": 0.93134349,
        "CALL_B_1": 0.93134349,
        "CALL_B_2": 0.93134349,
        "SWAN_E": 0.42795234,
    }

    for station in mms:
        for facility in station.facilities:
            if facility.emissions_factor_co2:
                facility_poll_map[
                    facility.code
                ] = facility.emissions_factor_co2

    session = SessionLocal()

    for fac_code, pol_value in facility_poll_map.items():
        facility = (
            session.query(Facility)
            .filter_by(code=fac_code)
            .filter_by(network_id="NEM")
            .one_or_none()
        )

        if not facility:
            print("could not find facility: {}".format(fac_code))
            continue

        facility.emissions_factor_co2 = pol_value
        session.add(facility)

    session.commit()


def import_pollution_cer():
    session = SessionLocal()

    r = http.get(CER_CSV)

    if not r.ok:
        logger.error("response failed: {}".format(CER_CSV))
        return False

    csv_content = decode_bytes(r.content).splitlines()
    csvreader = csv.DictReader(csv_content)

    swis_records = list(
        filter(
            lambda r: r["Grid"] == "SWIS"
            and r["Emission Intensity (t CO2-e/ MWh)"] != "0",
            csvreader,
        )
    )

    for rec in swis_records:
        station_name = station_name_cleaner(rec["Facility Name"])

        lookup = (
            session.query(Station).filter(Station.name == station_name).all()
        )

        if lookup:
            station = lookup.pop()
            print(
                "Found {} with code {} and {} facilities".format(
                    station.name, station.code, len(station.facilities)
                )
            )
        else:
            print("Could not find {}".format(station_name))


if __name__ == "__main__":
    import_pollution_cer()
