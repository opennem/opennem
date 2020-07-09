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

        join_key = None

        stations_updated = 0
        stations_added = 0
        generators_updated = 0
        generators_added = 0

        for generator_data in generators:
            facility = None

            station_name = name_normalizer(generator_data["station_name"])
            station_name_clean = station_name_cleaner(
                generator_data["station_name"]
            )
            participant_name = name_normalizer(generator_data["participant"])
            facility_region = name_normalizer(generator_data["region"])
            duid = normalize_duid(generator_data["duid"])
            reg_cap = clean_capacity(generator_data["reg_cap"])
            unit_no = (
                generator_data["unit_no"].strip()
                if type(generator_data["unit_no"]) is str
                else str(generator_data["unit_no"])
            )

            if join_key != station_name_clean:
                facility_station = None
                join_key = station_name_clean

            if not reg_cap:
                continue

            # See if we have the facility and unit
            facility = (
                s.query(NemFacility)
                .filter(NemFacility.region == facility_region)
                .filter(NemFacility.code == duid)
                .filter(NemFacility.unit_number == None)
                .one_or_none()
            )

            # Now try and find it without the unit number
            if not facility:
                facility = (
                    s.query(NemFacility)
                    .filter(NemFacility.region == facility_region)
                    .filter(NemFacility.code == duid)
                    .filter(NemFacility.unit_number == unit_no)
                    .one_or_none()
                )

                if facility:

                    if not facility.station:
                        raise Exception(
                            "Existing facility {} {} with no station .. unpossible.".format(
                                facility.id, facility.name
                            )
                        )

                    facility_station = facility.station

                    logger.info(
                        "REL: Found facility by DUID: {} {} {}".format(
                            facility.id, facility.name, facility_station.id
                        )
                    )

            if facility_station_join_by_name(station_name_clean):
                facility_station = (
                    s.query(NemStation)
                    .filter(NemStation.name_clean == station_name_clean)
                    .one_or_none()
                )

                # if not facility_station:
                #     raise Exception(
                #         "Trying to join {} by name but record not found".format(
                #             station_name
                #         )
                #     )

            # Done trying to find existing

            created_station = False
            created_facility = False

            if not facility_station:
                facility_station = NemStation(
                    name=station_name,
                    name_clean=station_name_clean,
                    nem_region=facility_region,
                    created_by="pipeline.nemstorerel",
                )

                s.add(facility_station)
                s.commit()

                created_station = True

            if not facility:
                facility = NemFacility(
                    name=station_name,
                    code=duid,
                    name_clean=station_name_clean,
                    region=facility_region,
                    created_by="pipeline.nemstorerel",
                )
                facility.station = facility_station

                created_facility = True

            if duid:
                facility.code = duid

            if not facility_station.participant:
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

                facility_station.participant = participant

            s.add(facility)
            s.commit()

            if not facility.participant_id:
                facility.participant = facility_station.participant

            # Assume all REL's are operating if we don't have a status
            if not facility.status_id:
                facility.status_id = "operating"

            facility.unit_size = clean_capacity(generator_data["unit_size"])
            facility.unit_number = unit_no
            facility.region = facility_region
            facility.name = station_name
            facility.name_clean = station_name_clean
            facility.nameplate_capacity = reg_cap

            fueltech = lookup_fueltech(
                generator_data["fuel_source_primary"],
                generator_data["fuel_source_descriptor"],
                generator_data["tech_primary"],
                generator_data["tech_primary_descriptor"],
            )

            # Log that we have a new fueltech
            if fueltech and fueltech != facility.fueltech_id:
                logger.warn(
                    "Fueltech mismatch for {} {}: prev {} new {}".format(
                        facility.name_clean,
                        facility.code,
                        facility.fueltech_id,
                        fueltech,
                    )
                )

            facility.fueltech_id = fueltech

            s.add(facility)
            s.commit()

            if created_station:
                logger.info(
                    "{} station with name {} and id {}".format(
                        "Created" if created_station else "Updated",
                        facility_station.name_clean,
                        facility_station.id,
                    )
                )

            if created_facility:
                logger.info(
                    "{} facility with name {} and duid {} and id {}".format(
                        "Created" if created_facility else "Updated",
                        facility.name_clean,
                        facility.code,
                        facility.id,
                    )
                )

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
                s.query(NemStation)
                .filter(NemStation.name_clean == facility_name_clean)
                .first()
            )

        if duid:
            try:
                facility = (
                    s.query(NemFacility)
                    .filter(NemFacility.code == duid)
                    .filter(NemFacility.region == facility_region)
                    # .filter(NemFacility.nameplate_capacity != None)
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
                s.query(NemFacility)
                .filter(NemFacility.region == facility_region)
                .filter(NemFacility.name_clean == facility_name_clean)
                # .filter(NemFacility.fueltech_id == facility_fueltech)
                .filter(NemFacility.code == None)
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
            facility_station = NemStation(
                name=item["Name"],
                name_clean=facility_name_clean,
                nem_region=facility_region,
                created_by="pipeline.nem.facility.gi",
            )

            s.add(facility_station)

            created_station = True

        if not facility:
            facility = NemFacility(created_by="pipeline.nem.facility.gi")
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
