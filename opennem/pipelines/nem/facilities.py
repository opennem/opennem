import json
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from opennem.db.models.opennem import (
    FacilityStatus,
    NemFacility,
    NemParticipant,
)
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


NEM_FUELTECH_MAP = {
    "wind": "wind",
    "solar": "solar_utility",
    "gas": "gas_ccgt",
    "landfill gas": "bioenergy_biogas",
    "biomass": "bioenergy_biomass",
    "coal": "coal_black",
    "distillate": "distillate",
}


def get_nem_fueltech(wem_fueltype):
    ft = wem_fueltype.lower()

    if not ft in NEM_FUELTECH_MAP.keys():
        logger.error("Found fueltech {} with no mapping".format(ft))
        return None

    return NEM_FUELTECH_MAP[ft]


def get_nem_status(unit_status):
    if unit_status == "In Service":
        return "operating"

    logger.error(
        "Could not find status for unit status: {}".format(unit_status)
    )
    return None


def company_name_trim(company_name):
    return company_name.replace("Pty Ltd", "").replace("Ltd", "").strip()


class NemStoreFacility(DatabaseStoreBase):
    def parse_interval(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        if item["Status"] != "Existing Plant":
            return item

        if item["FuelType"] in ["Natural Gas Pipeline"]:
            return item

        participant_name = company_name_trim(item["Owner"])

        participant = (
            s.query(NemParticipant)
            .filter(NemParticipant.name == participant_name)
            .one_or_none()
        )

        if not participant:
            participant = NemParticipant(name=participant_name)

            s.add(participant)
            s.commit()
            logger.info("Added new partipant: {}".format(participant_name))

        facility = None

        if item["DUID"]:
            duid = item["DUID"]

            facility = (
                s.query(NemFacility)
                .filter(NemFacility.code == duid)
                .one_or_none()
            )

        if not facility:
            facility = (
                s.query(NemFacility)
                .filter(NemFacility.region == item["Region"])
                .filter(NemFacility.name == item["Name"])
                .filter(NemFacility.nameplate_capacity == item["NameCapacity"])
                .one_or_none()
            )

        if not facility:
            facility = NemFacility()

        if item["DUID"]:
            facility.code = item["DUID"]

        facility.participant = participant
        facility.region = item["Region"]
        facility.name = item["Name"]

        if "FuelType" in item and item["FuelType"]:
            facility.fueltech_id = get_nem_fueltech(item["FuelType"])

        facility.nameplate_capacity = item["NameCapacity"]
        facility.status_id = get_nem_status(item["UnitStatus"])

        try:
            s.add(facility)
            s.commit()
        except Exception as e:
            logger.error(e)
        finally:
            s.close()
