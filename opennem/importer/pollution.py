import csv
import logging

from opennem.core.loader import load_data
from opennem.core.normalizers import clean_float, normalize_duid
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility
from opennem.importer.mms import mms_import

logger = logging.getLogger(__name__)


def import_pollution_mms() -> None:
    mms = mms_import()

    facility_poll_map = {
        "CALL_A_4": 0.93134349,
        "CALL_B_1": 0.93134349,
        "CALL_B_2": 0.93134349,
        "SWAN_E": 0.42795234,
        "OSB-AG": 0.544686,
    }

    for station in mms:
        for facility in station.facilities:
            if facility.emissions_factor_co2 and not facility.code.endswith(
                "NL1"
            ):
                facility_poll_map[facility.code] = {
                    "intensity": facility.emissions_factor_co2,
                    "name": station.name,
                    "fueltech": facility.fueltech.code
                    if facility.fueltech
                    else "",
                }

    session = SessionLocal()

    for fac_code, pol_value in facility_poll_map.items():
        facility = (
            session.query(Facility)
            .filter_by(code=fac_code)
            .filter_by(network_id="NEM")
            .one_or_none()
        )

        if not facility:
            logger.info(
                "could not find facility: {} {}".format(fac_code, pol_value)
            )

            continue

        facility.emissions_factor_co2 = clean_float(pol_value)
        session.add(facility)

    session.commit()

    return None


def import_pollution_wem() -> None:
    session = SessionLocal()

    content = load_data(
        "wem_pollutions.csv", from_project=True, skip_loaders=True
    )

    csv_content = content.splitlines()
    csvreader = csv.DictReader(csv_content)

    for rec in csvreader:
        facility_code = normalize_duid(rec["facility_code"])
        emissions_intensity = clean_float(rec["emission_intensity_c02"])

        if not facility_code:
            logger.info("No emissions intensity for {}".format(facility_code))
            continue

        facility = (
            session.query(Facility).filter_by(code=facility_code).one_or_none()
        )

        if not facility:
            logger.info("No stored facility for {}".format(facility_code))
            continue

        facility.emissions_factor_co2 = emissions_intensity
        session.add(facility)
        logger.info(
            "Updated {} to {}".format(facility_code, emissions_intensity)
        )

    session.commit()

    return None


if __name__ == "__main__":
    import_pollution_mms()
