import json
import logging
from datetime import datetime
from itertools import groupby

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
from opennem.core.unit_codes import get_unit_code
from opennem.core.unit_parser import parse_unit_duid
from opennem.db.models.opennem import (
    Facility,
    FacilityStatus,
    Participant,
    Station,
)
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def has_unique_duid(units: list) -> bool:
    duids = set([i["duid"] for i in units])
    return len(duids) == len(units)


def get_unique_duid(units: list) -> str:
    if not type(units) is list or len(units) < 1:
        return None

    first_record = units[0]

    return (
        normalize_duid(first_record["duid"])
        if "duid" in first_record
        else None
    )


def get_station_record_from_facilities(units: list):
    if not type(units) is list or len(units) < 1:
        raise Exception("Passed units list with no units ..")

    if len(units) == 1:
        return units[0]

    for u in units:
        cap = clean_capacity(u["reg_cap"])
        duid = normalize_duid(u["duid"])

        if cap:
            return u

    return units[0]


class RegistrationExemptionGrouperPipeline(object):
    """
        This is the first-pass pipeline of the AEMO Registration and Exemptions list

        It groups by clean station name

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if not "generators" in item:
            raise Exception("No generators found in item pipeline failed")

        generators = item["generators"]

        # Add clean station names and if group_by name
        generators = [
            {
                **i,
                "name": station_name_cleaner(i["station_name"]),
                "name_join": False
                if facility_station_join_by_name(
                    station_name_cleaner(i["station_name"])
                )
                else i["duid"],
            }
            for i in generators
        ]

        # sort by name

        generators_grouped = {}

        for k, v in groupby(
            generators, key=lambda v: (v["name"], v["name_join"])
        ):
            key = k[0]
            if not key in generators_grouped:
                generators_grouped[key] = []

            generators_grouped[key] += list(v)

        return {**item, "generators": generators_grouped}


class RegistrationExemptionStorePipeline(DatabaseStoreBase):
    """
        This pipeline is the second pass of the AEMO NEM REL List

        It sorts out whats new, what is updated, units and updating the database

    """

    # Cache of participant keys
    participant_keys = {}

    def process_participants(self, participants):
        s = self.session()

        for participant_data in participants:
            participant_name = participant_data["name"].strip()

            try:
                participant = (
                    s.query(Participant)
                    .filter(Participant.name == participant_name)
                    .one_or_none()
                )
            except MultipleResultsFound as e:
                logger.info(
                    "Found multiple participants with name {}".format(
                        participant_name
                    )
                )

                participant = (
                    s.query(Participant)
                    .filter(Participant.name == participant_name)
                    .first()
                )

            if not participant:
                participant = Participant(name=participant_name)

            participant.name_clean = participant_name_filter(participant_name)
            participant.abn = participant_data["abn"]

            s.add(participant)

            logger.info(
                "Found new NEM participant: {}".format(participant_name)
            )
            self.participant_keys[participant_name] = participant

            facility = None

        s.commit()

    def process_facilities(self, generators):
        s = self.session()

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

            if not generator_data["dispatch_type"] == "Generator":
                continue

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

            # @TODO insert into units table
            if not reg_cap:
                continue

            # See if we have the facility by duid
            facility = (
                s.query(Facility).filter(Facility.code == duid).one_or_none()
            )

            if not facility:
                logger.info(
                    "Skipping: Could not find facility {} ({})".format(
                        station_name, duid
                    )
                )
                continue

            facility_station = facility.station

            # Done trying to find existing

            created_station = False
            created_facility = False

            if not facility_station:
                facility_station = Station(
                    name=station_name,
                    name_clean=station_name_clean,
                    nem_region=facility_region,
                    created_by="pipeline.nemstorerel",
                )

                # s.add(facility_station)
                # s.commit()

                created_station = True

            if not facility:
                facility = Facility(
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

        if not type(generators) is dict:
            raise Exception(
                "Require grouped generators for this pipeline step. Run RegistrationExemptionGrouperPipeline"
            )

        self.process_generators(generators)

    def process_generators(self, generators):
        s = self.session()

        stations_updated = 0
        stations_added = 0
        generators_updated = 0
        generators_added = 0

        from pprint import pprint

        for station_name, facilities in generators.items():
            facility = None
            facility_station = None
            created_station = False
            created_facility = False

            duid_unique = has_unique_duid(facilities)
            facility_count = len(facilities)

            logger.debug(station_name)
            logger.debug(facilities)

            # Step 1. Find the station
            # First by duid if it's unique
            duid = get_unique_duid(facilities)

            # This is the most suitable unit record to use for the station
            # see helper above
            facility_station_record = get_station_record_from_facilities(
                facilities
            )

            if duid and duid_unique and facility_count == 1:

                facility_lookup = (
                    s.query(Facility)
                    .filter(Facility.network_code == duid)
                    .one_or_none()
                )

                if facility_lookup and facility_lookup.station:
                    facility_station = facility_lookup.station

            if (
                duid
                and (duid_unique and facility_count > 1)
                or not duid_unique
            ):

                facility_lookup = (
                    s.query(Facility)
                    .filter(Facility.network_code == duid)
                    .first()
                )

                if facility_lookup and facility_lookup.station:
                    facility_station = facility_lookup.station

            # Create one as it doesm't exist
            if not facility_station:
                facility_station = Station(
                    name=station_name,
                    network_name=name_normalizer(
                        facility_station_record["station_name"]
                    ),
                    network_id="NEM",
                    created_by="pipeline.aemo.registration_exemption",
                )

                s.add(facility_station)
                created_station = True

            # Step 2. Add the facilities/units to the station
            # Now that we have a station or created one ..

            # Step go through the facility records we got ..
            for facility_record in facilities:
                network_name = name_normalizer(facility_record["station_name"])
                participant_name = name_normalizer(
                    facility_record["participant"]
                )
                facility_region = name_normalizer(facility_record["region"])
                duid = normalize_duid(facility_record["duid"])
                reg_cap = clean_capacity(facility_record["reg_cap"])
                unit = parse_unit_duid(facility_record["unit_no"], duid)
                unit_size = clean_capacity(facility_record["unit_size"])
                unit_code = get_unit_code(
                    unit, duid, facility_station_record["station_name"]
                )
                facility_status = "operating"
                fueltech = lookup_fueltech(
                    facility_record["fuel_source_primary"],
                    facility_record["fuel_source_descriptor"],
                    facility_record["tech_primary"],
                    facility_record["tech_primary_descriptor"],
                )

                # check if we have it by ocode first
                facility = (
                    s.query(Facility)
                    .filter(Facility.code == unit_code)
                    .one_or_none()
                )

                # If the duid is unique then we have no issues on which to join/create
                if duid and duid_unique and not facility:
                    facility = (
                        s.query(Facility)
                        .filter(Facility.network_code == duid)
                        .one_or_none()
                    )

                # If the duid is not unique then we need to figure things out ..
                if duid and not duid_unique and not facility:
                    facility_lookup = (
                        s.query(Facility)
                        .filter(Facility.network_code == duid)
                        # Not having a code means we haven't written to this record yet so we'll use it
                        .filter(Facility.code == None)
                        .all()
                    )

                    facility_db_count = len(facility_lookup)

                    logging.debug(
                        "Non unique duid: {} with {} in database and {} in facility duid is {}".format(
                            station_name,
                            facility_db_count,
                            facility_count,
                            duid,
                        )
                    )

                    if len(facility_lookup) > 0:
                        facility = facility_lookup.pop()

                if not facility:
                    facility = Facility(
                        network_code=duid,
                        created_by="pipeline.aemo.registration_exemption",
                    )
                    created_facility = True

                # Sanity checking
                if len(unit_code) < 3:
                    raise Exception(
                        "Unit code {} is invalid. For station {} with duid {}".format(
                            unit_code, station_name, duid
                        )
                    )

                #
                facility.code = unit_code
                facility.fueltech_id = fueltech
                facility.network_code = duid
                facility.network_region = facility_region
                facility.network_name = network_name

                facility.capacity_registered = reg_cap

                facility.unit_id = unit.id
                facility.unit_number = unit.number
                facility.unit_size = unit_size
                facility.unit_alias = unit.alias
                facility.unit_capacity = unit_size

                # Assume all REL's are operating if we don't have a status
                facility.status_id = "operating"

                facility.station = facility_station

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

                if not created_facility:
                    facility.updated_by = (
                        "pipeline.aemo.registration_exemption"
                    )

                s.add(facility)
                s.commit()

            if created_station:
                logger.info(
                    "{} station with name {} and id {}".format(
                        "Created" if created_station else "Updated",
                        facility_station.name,
                        facility_station.id,
                    )
                )

            if created_facility:
                logger.info(
                    "{} facility with name {} and duid {} and id {}".format(
                        "Created" if created_facility else "Updated",
                        facility.network_name,
                        facility.code,
                        facility.network_code,
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
