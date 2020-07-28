import json
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.sql import text

from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.facilitystatus import lookup_facility_status
from opennem.core.fueltechs import lookup_fueltech
from opennem.core.normalizers import (
    clean_capacity,
    name_normalizer,
    normalize_duid,
    participant_name_filter,
    station_name_cleaner,
)
from opennem.db.models.opennem import (
    Facility,
    FacilityStatus,
    Participant,
    Station,
)
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class NemStoreGI(DatabaseStoreBase):
    def parse_interval(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        if item["FuelType"] in ["Natural Gas Pipeline"]:
            return {}

        if (
            item["UnitStatus"]
            in [
                "Publically Announced",
                "Upgrade",
                "Emerging",
                "Expansion",
                "Maturing",
            ]
            or not item["UnitStatus"]
        ):
            return {}

        participant_name = name_normalizer(item["Owner"])

        # Funky case of Todae solar where they put their name in the

        participant = (
            s.query(Participant)
            .filter(Participant.name == participant_name)
            .one_or_none()
        )

        if not participant:
            participant = Participant(
                name=participant_name,
                name_clean=participant_name_filter(participant_name),
            )

            s.add(participant)
            s.commit()
            logger.info(
                "GI: Added new partipant to NEM database: {}".format(
                    participant_name
                )
            )

        facility = None
        facility_station = None

        facility_name = name_normalizer(item["Name"])
        facility_name_clean = station_name_cleaner(item["Name"])
        duid = normalize_duid(item["DUID"])
        facility_status = lookup_facility_status(item["UnitStatus"])
        facility_region = item["Region"]
        facility_fueltech = (
            lookup_fueltech(item["FuelType"], techtype=item["TechType"])
            if ("FuelType" in item and item["FuelType"])
            else None
        )

        if facility_station_join_by_name(facility_name_clean):
            facility_station = (
                s.query(Station)
                .filter(Station.name_clean == facility_name_clean)
                .first()
            )

        if duid:
            try:
                facility = (
                    s.query(Facility)
                    .filter(Facility.code == duid)
                    .filter(Facility.region == facility_region)
                    # .filter(Facility.nameplate_capacity != None)
                    .one_or_none()
                )
            except MultipleResultsFound:
                logger.warn(
                    "Multiple results found for duid : {}".format(duid)
                )

            if facility:
                if not facility.station:
                    raise Exception(
                        "GI: Existing facility {} {} with no station .. unpossible.".format(
                            facility.id, facility.name
                        )
                    )

                if facility.station and not facility_station:
                    facility_station = facility.station

                logger.info(
                    "GI: Found facility by DUID: {} {} {}".format(
                        facility.id, facility.name, facility_station.id
                    )
                )

        if not duid:
            facility_lookup = (
                s.query(Facility)
                .filter(Facility.region == facility_region)
                .filter(Facility.name_clean == facility_name_clean)
                # .filter(Facility.fueltech_id == facility_fueltech)
                .filter(Facility.code == None)
                .first()
            )

            if facility_lookup:
                if not facility_lookup.station:
                    raise Exception(
                        "GI: Existing facility {} {} with no station .. unpossible.".format(
                            facility.id, facility.name
                        )
                    )

                if facility_lookup.station and not facility_station:
                    facility_station = facility_lookup.station

                # logger.info(
                #     "GI: Found facility by no duid name fueltech and region : {} {} {}".format(
                #         facility.id, facility.name, facility_station.id
                #     )
                # )

        # Done trying to find existing

        created_station = False
        created_facility = False

        if not facility_station:
            facility_station = Station(
                name=item["Name"],
                name_clean=facility_name_clean,
                nem_region=facility_region,
                created_by="pipeline.nem.facility.gi",
            )

            s.add(facility_station)

            created_station = True

        if not facility:
            facility = Facility(created_by="pipeline.nem.facility.gi")
            facility.station = facility_station

            created_facility = True

        if duid:
            facility.code = duid

        facility.participant = participant

        if not facility.region:
            facility.region = facility_region

        if not facility.name:
            facility.name = name_normalizer(item["Name"])

        if not facility.name_clean:
            facility.name_clean = station_name_cleaner(item["Name"])

        # @TODO parse units into ints
        facility.unit_number = item["Units"]

        if not facility.fueltech_id and facility_fueltech:
            facility.fueltech_id = facility_fueltech

        if facility.fueltech_id is None:
            logger.error("Could not find fueltech for: {}".format(item))

        if not facility.nameplate_capacity:
            facility.nameplate_capacity = clean_capacity(
                item["UpperCapacity"] or item["NameCapacity"]
            )

        facility.status_id = facility_status

        if facility_station and not facility.station:
            facility.station = facility_station

        if facility.status_id is None:
            raise Exception(
                "GI: Failed to map status ({}) on row: {}".format(
                    facility.status_id, item
                )
            )

        if created_station:
            logger.info(
                "GI: {} station with name {} and id {}".format(
                    "Created" if created_station else "Updated",
                    facility_station.name_clean,
                    facility_station.id,
                )
            )

        if created_facility:
            logger.info(
                "GI: {} facility with name {} and duid {} and id {}".format(
                    "Created" if created_facility else "Updated",
                    facility.name_clean,
                    facility.code,
                    facility.id,
                )
            )

        try:
            s.add(facility)
            s.commit()
        except Exception as e:
            logger.error(e)
            raise e
        finally:
            s.close()

        return {
            "name": name_normalizer(item["Name"]),
            "status": item["UnitStatus"],
            "status_id": lookup_facility_status(item["UnitStatus"]),
        }


class NemStoreMMS(DatabaseStoreBase):
    def parse_interval(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        print(item)
