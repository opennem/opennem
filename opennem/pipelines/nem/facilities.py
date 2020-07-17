import json
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

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
    FacilityStatus,
    NemFacility,
    NemParticipant,
    NemStation,
)
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class NemStoreREL(DatabaseStoreBase):
    """
        This pipeline stores items from the NEM REL spreadsheet.

        It sends in the entire sheet of participants and generators in a dict item

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        if not "generators" in item and type(item["generators"]) is not list:
            raise Exception("Invalid item - no generators located")

        if (
            not "participants" in item
            and type(item["participants"]) is not list
        ):
            raise Exception("Invalid item - no generators located")

        generators = item["generators"]
        participants = item["participants"]
        participant_keys = {}

        from pprint import pprint

        for participant_data in participants:
            participant_name = participant_data["name"].strip()

            participant = (
                s.query(NemParticipant)
                .filter(NemParticipant.name == participant_name)
                .one_or_none()
            )

            if not participant:
                participant = NemParticipant(name=participant_name)

            participant.name_clean = participant_name_filter(participant_name)
            participant.abn = participant_data["abn"]

            s.add(participant)
            s.commit()
            logger.info(
                "Added new NEM partipant to database: {}".format(
                    participant_name
                )
            )
            participant_keys[participant_name] = participant

            facility = None

        station = None
        participant = None
        station_current = None
        generators_updated = 0

        for generator_data in generators:
            station_name = name_normalizer(generator_data["station_name"])
            participant_name = name_normalizer(generator_data["participant"])
            nem_region = name_normalizer(generator_data["region"])
            duid = normalize_duid(generator_data["duid"])

            # pprint(generator_data)

            if station_name != station_current:
                station = (
                    s.query(NemStation)
                    .filter(NemStation.name == station_name)
                    .filter(NemStation.nem_region == nem_region)
                    .one_or_none()
                )

                if not station:
                    logger.debug(
                        "Could not find station {} adding to database".format(
                            station_name
                        )
                    )
                    station = NemStation(
                        name=station_name,
                        name_clean=station_name_cleaner(station_name),
                        nem_region=nem_region,
                    )

                if not station.participant:
                    if participant_name in participant_keys:
                        participant = participant_keys[participant_name]

                    if not participant:
                        participant = (
                            s.query(NemParticipant)
                            .filter(NemParticipant.name == participant_name)
                            .one_or_none()
                        )

                    if not participant:
                        raise Exception(
                            "Could not locate existing participant '{}' for station {}".format(
                                participant_name, station_name
                            )
                        )

                    station.participant = participant

                s.add(station)
                s.commit()
                logger.info(
                    "Added new NEM station to database: {}".format(
                        station_name
                    )
                )

            # generator = (
            # s.query(NemFacility)
            # .filter(NemFacility.code == duid)
            # .one_or_none()
            # )

            # if not generator:
            # generator = (
            # s.query(NemFacility)
            # .filter(NemFacility.code == duid)
            # .one_or_none()
            # )

            # if not generator:
            generator = NemFacility(code=duid, station=station)

            if not generator.participant_id:
                generator.participant = station.participant

            generator.region = generator_data["region"]
            generator.name = generator_data["station_name"].strip()
            generator.name_clean = station_name_cleaner(
                generator_data["station_name"]
            )
            generator.nameplate_capacity = clean_capacity(
                generator_data["reg_cap"]
            )
            generator.region = generator_data["region"]
            generator.fueltech_id = lookup_fueltech(
                generator_data["fuel_source_primary"],
                generator_data["tech_primary_descriptor"],
                generator_data["fuel_source_descriptor"],
            )
            generator.status_id = "operating"
            generator.unit_size = clean_capacity(generator_data["unit_size"])
            generator.unit_number = generator_data["unit_no"]

            s.add(generator)
            s.commit()
            generators_updated += 1
            logger.info(
                "Added generator to database: {}".format(generator.name)
            )

        print(
            "Added {} of {} generators".format(
                generators_updated, len(generators)
            )
        )
        return 0


class NemStoreFacility(DatabaseStoreBase):
    def parse_interval(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        # if item["Status"] not in ["Existing Plant", "Project"]:
        # return item

        if item["FuelType"] in ["Natural Gas Pipeline"]:
            return {}

        if (
            item["UnitStatus"]
            in ["Publically Announced", "Upgrade", "Emerging", "Expansion",]
            or not item["UnitStatus"]
        ):
            return {}

        participant_name = name_normalizer(item["Owner"])

        participant = (
            s.query(NemParticipant)
            .filter(NemParticipant.name == participant_name)
            .one_or_none()
        )

        if not participant:
            participant = NemParticipant(name=participant_name)

            s.add(participant)
            s.commit()
            logger.info(
                "Added new partipant to NEM database: {}".format(
                    participant_name
                )
            )

        facility = None
        duid = normalize_duid(item["DUID"])
        facility_status = lookup_facility_status(item["UnitStatus"])
        facility_station = None

        if duid:
            facility = (
                s.query(NemFacility)
                .filter(NemFacility.code == duid)
                .filter(NemFacility.region == item["Region"])
                .filter(NemFacility.nameplate_capacity != None)
                .first()
            )

            if facility:
                facility_station = facility.station_id

        if not duid:
            facility = (
                s.query(NemFacility)
                .filter(NemFacility.region == item["Region"])
                .filter(NemFacility.name == item["Name"])
                .filter(NemFacility.nameplate_capacity != None)
                .first()
            )

        if not facility:
            facility = NemFacility()

            if facility_station:
                facility.station_id = facility_station

        if not facility.station:
            station_name = item["Name"]
            nem_region = item["Region"]

            station = NemStation(
                name=station_name,
                name_clean=station_name_cleaner(station_name),
                nem_region=nem_region,
            )

            s.add(station)
            s.commit()

            facility.station = station

        if duid:
            facility.code = duid

        facility.participant = participant

        if not facility.region:
            facility.region = item["Region"]

        if not facility.name:
            facility.name = name_normalizer(item["Name"])

        facility.unit_number = item["Units"]

        if "FuelType" in item and item["FuelType"]:
            facility.fueltech_id = lookup_fueltech(
                item["FuelType"], item["TechType"]
            )

        if not facility.nameplate_capacity:
            facility.nameplate_capacity = clean_capacity(
                item["UpperCapacity"] or item["NameCapacity"]
            )

        facility.status_id = facility_status

        if facility.status_id is None:
            raise Exception(
                "Failed to map status ({}) on row: {}".format(
                    facility.status_id, item
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
