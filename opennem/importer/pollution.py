import csv

from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility
from opennem.importer.mms import mms_import
from opennem.utils.http import http

CER_CSV = "http://www.cleanenergyregulator.gov.au/DocumentAssets/Documents/Greenhouse%20and%20energy%20information%20for%20designated%20generation%20facilities%202018-19%20.csv"


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
    pass


if __name__ == "__main__":
    import_pollution_cer()
