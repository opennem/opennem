import csv
import logging

from opennem.core.loader import load_data
from opennem.core.normalizers import clean_float, normalize_duid
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility
from opennem.importer.mms import mms_import

logger = logging.getLogger(__name__)


def import_mms_emissions() -> None:
    # mms = mms_import()

    facility_poll_map = {
        "APS": 1.228625,
        "CALL_A_4": 0.93134349,
        "CALL_B_1": 0.93134349,
        "CALL_B_2": 0.93134349,
        "SWAN_E": 0.42795234,
        "OSB-AG": 0.544686,
        "HWPS1": 1.558001,
        "HWPS2": 1.558001,
        "HWPS3": 1.558001,
        "HWPS4": 1.558001,
        "COLNSV_3": 1.191769,
        "MM3": 1.162987,
        "MM4": 1.162987,
        "NPS1": 1.130635,
        "NPS2": 1.130635,
        "NPSNL2": 1.130635,
        "PLAYFB1": 1.509041,
        "PLAYFB2": 1.509041,
        "PLAYFB3": 1.509041,
        "PLAYFB4": 1.509041,
        "PLAYB-AG": 1.509041,
        "COLNSV_4": 1.191769,
        "COLNSV_5": 1.191769,
        "HWPS7": 1.558001,
        "HWPS8": 1.558001,
        "SWAN_B_1": 1.091,
        "SWAN_B_2": 1.091,
        "SWAN_B_3": 1.091,
        "SWAN_B_4": 1.091,
        "CALL_A_2": 1.328,
        "CALL_A_4": 1.328,
        "COLNSV_1": 1.191769,
        "COLNSV_2": 1.191769,
        "HWPS5": 1.558001,
        "HWPS6": 1.558001,
        "WW7": 1.030046,
        "WW8": 1.030046,
        # from wem
        "KWINANA_C5": 0.877,
        "KWINANA_C5": 0.877,
        # from reports
        "REDBANK1": 1.2,
        # from https://web.archive.org/web/20111002115520/http://carma.org/company/detail/6264
        "MOR1": 2.79,
        "MOR2": 2.79,
        "MOR3": 2.79,
    }

    # for station in mms:
    #     for facility in station.facilities:
    #         if facility.emissions_factor_co2 and not facility.code.endswith(
    #             "NL1"
    #         ):
    #             facility_poll_map[facility.code] = {
    #                 "intensity": facility.emissions_factor_co2,
    #                 "name": station.name,
    #                 "fueltech": facility.fueltech.code
    #                 if facility.fueltech
    #                 else "",
    #             }

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


def import_emissions_csv() -> None:
    EMISSION_MAPS = [
        {"filename": "wem_emissions.csv", "network": "WEM"},
        {"filename": "nem_emissions.csv", "network": "NEM"},
    ]

    for m in EMISSION_MAPS:
        import_emissions_map(m["filename"], m["network"])


def import_emissions_map(file_name: str, network_id: str) -> None:
    session = SessionLocal()

    content = load_data(file_name, from_project=True, skip_loaders=True)

    csv_content = content.splitlines()
    csvreader = csv.DictReader(csv_content)

    for rec in csvreader:
        facility_code = normalize_duid(rec["facility_code"])
        emissions_intensity = clean_float(rec["emissions_factor_co2"])

        if not facility_code:
            logger.info("No emissions intensity for {}".format(facility_code))
            continue

        facility = (
            session.query(Facility)
            .filter_by(code=facility_code)
            .filter_by(network_id=network_id)
            .one_or_none()
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
    import_emissions_csv()
    import_mms_emissions()
