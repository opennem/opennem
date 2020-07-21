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

        stations_updated = 0
        stations_added = 0
        generators_updated = 0
        generators_added = 0

        for generator_data in generators:
            station_name = name_normalizer(generator_data["station_name"])
            participant_name = name_normalizer(generator_data["participant"])
            nem_region = name_normalizer(generator_data["region"])
            duid = normalize_duid(generator_data["duid"])
            reg_cap = clean_capacity(generator_data["reg_cap"])
            unit_no = (
                generator_data["unit_no"].strip()
                if type(generator_data["unit_no"]) is str
                else str(generator_data["unit_no"])
            )

            if not reg_cap:
                continue

            # See if we have the facility and unit
            facility = (
                s.query(NemFacility)
                .filter(NemFacility.region == nem_region)
                .filter(NemFacility.code == duid)
                .filter(NemFacility.unit_number == unit_no)
                .one_or_none()
            )

            # Now try and find it without the unit number
            if not facility:
                facility = (
                    s.query(NemFacility)
                    .filter(NemFacility.region == nem_region)
                    .filter(NemFacility.code == duid)
                    .one_or_none()
                )

            # If we still don't have it .. create it and the station
            if not facility:
                logger.info(
                    "Could not find station {} adding to database".format(
                        station_name
                    )
                )
                facility = NemFacility(
                    name=station_name,
                    code=duid,
                    name_clean=station_name_cleaner(station_name),
                    region=nem_region,
                )
                station = NemStation(
                    name=station_name,
                    name_clean=station_name_cleaner(station_name),
                )
                facility.station = station

            station = facility.station

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

            s.add(facility)
            s.commit()

            if not facility.participant_id:
                facility.participant = station.participant

            # Assume all REL's are operating if we don't have a status
            if not facility.status_id:
                facility.status_id = "operating"

            facility.unit_size = clean_capacity(generator_data["unit_size"])
            facility.unit_number = unit_no
            facility.region = nem_region
            facility.name = station_name
            facility.name_clean = station_name_cleaner(
                generator_data["station_name"]
            )
            facility.nameplate_capacity = reg_cap

            fueltech = lookup_fueltech(
                generator_data["fuel_source_primary"],
                generator_data["tech_primary"],
                generator_data["tech_primary_descriptor"],
                generator_data["fuel_source_descriptor"],
            )

            # handle fueltechs and conflicts
            if not facility.fueltech_id:
                facility.fueltech_id = fueltech
            else:
                # Log that we have a new fueltech
                if fueltech and fueltech != facility.fueltech_id:
                    logger.error(
                        "Fueltech mismatch for {} {}: prev {} new {}".format(
                            facility.name_clean,
                            facility.code,
                            facility.fueltech_id,
                            fueltech,
                        )
                    )

            s.add(facility)
            s.commit()

            generators_updated += 1

        print(
            "NEM REL Pipeline: Added {} stations, updated {} stations. Added {}, updated {} generators of {} total".format(
                stations_added,
                stations_updated,
                generators_added,
                generators_updated,
                len(generators),
            )
        )

        return 0


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
            s.query(NemParticipant)
            .filter(NemParticipant.name == participant_name)
            .one_or_none()
        )

        if not participant:
            participant = NemParticipant(
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
        duid = normalize_duid(item["DUID"])
        facility_status = lookup_facility_status(item["UnitStatus"])
        facility_region = item["Region"]
        facility_station = None

        if duid:
            facility = (
                s.query(NemFacility)
                .filter(NemFacility.code == duid)
                .filter(NemFacility.region == facility_region)
                .filter(NemFacility.nameplate_capacity != None)
                .first()
            )

            if not facility.station:
                raise Exception(
                    "Existing facility {} {} with no station .. unpossible.".format(
                        facility.id, facility.name
                    )
                )

            facility_station = facility.station

            logger.info(
                "RI: Found facility by DUID: {} {} {}".format(
                    facility.id, facility.name, facility_station.id
                )
            )

        if not duid:
            facility = (
                s.query(NemFacility)
                .filter(NemFacility.region == facility_region)
                .filter(
                    NemFacility.name_clean
                    == station_name_cleaner(item["Name"])
                )
                .filter(NemFacility.nameplate_capacity != None)
                .first()
            )

            if not facility.station:
                raise Exception(
                    "Existing facility {} {} with no station .. unpossible.".format(
                        facility.id, facility.name
                    )
                )

            facility_station = facility.station

            logger.info(
                "RI: Found facility by name and no nameplate: {} {} {}".format(
                    facility.id, facility.name, facility_station.id
                )
            )

        station_name = station_name_cleaner(item["Name"])

        if not facility_station:
            facility_station = (
                s.query(NemStation)
                .filter(NemStation.name_clean == station_name)
                .filter(NemStation.nem_region == facility_region)
                .one_or_none()
            )

            if not facility.station:
                raise Exception(
                    "Existing facility {} {} with no station .. unpossible.".format(
                        facility.id, facility.name
                    )
                )

            facility_station = facility.station

            logger.info(
                "RI: Found facility by name: {} {} {}".format(
                    facility.id, facility.name, facility_station.id
                )
            )

        # Done trying to find existing

        created_station = False
        created_facility = False

        if not facility_station:
            facility_station = NemStation(
                name=item["Name"],
                name_clean=station_name,
                nem_region=facility_region,
            )

            s.add(facility_station)
            s.commit()

            created_station = True

        if not facility:
            facility = NemFacility()
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

        if (
            "FuelType" in item
            and item["FuelType"]
            and not facility.fueltech_id
        ):
            facility.fueltech_id = lookup_fueltech(
                item["FuelType"], item["TechType"]
            )

        if facility.fueltech_id is None:
            logger.error("Could not find fueltech for: {}".format(item))

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

        logger.error(
            "{} station with name {} and id {}".format(
                "Created" if created_station else "Updated",
                facility_station.name_clean,
                facility_station.id,
            )
        )
        logger.error(
            "{} facility with name {} and duid {} and id {}".format(
                "Created" if craeted_facility else "Updated",
                station.name_clean,
                station.code,
                station.id,
            )
        )

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
