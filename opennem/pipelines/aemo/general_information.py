import json
import logging
from datetime import datetime
from itertools import groupby
from typing import List, Optional

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.sql import text

from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.facilitystatus import map_aemo_facility_status
from opennem.core.fueltechs import lookup_fueltech
from opennem.core.normalizers import (
    clean_capacity,
    name_normalizer,
    normalize_aemo_region,
    normalize_duid,
    participant_name_filter,
    station_name_cleaner,
)
from opennem.core.station_duid_map import (
    facility_has_station_remap,
    facility_map_station,
)
from opennem.core.unit_codes import get_unit_code
from opennem.core.unit_parser import parse_unit_duid
from opennem.db.models.opennem import (
    Facility,
    FacilityStatus,
    Participant,
    Station,
)
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


FACILITY_INVALID_STATUS = [
    "Publically Announced",
    "Upgrade",
    "Emerging",
    "Expansion",
    "Maturing",
]


def get_station_record_from_facilities(units: list):
    if not type(units) is list or len(units) < 1:
        raise Exception("Passed units list with no units ..")

    if len(units) == 1:
        return units[0]

    for u in units:
        cap = clean_capacity(u["NameCapacity"])
        duid = normalize_duid(u["duid"])

        if cap:
            return u

    return units[0]


def record_get_station_name(facilities) -> str:
    station_name = facilities[0]["station_name"]

    return station_name


def has_unique_duid(units: List) -> bool:
    duids = set([i["duid"] for i in units])
    return len(duids) == len(units)


def get_unique_duid(units: List) -> Optional[str]:
    if len(units) < 1:
        return None

    first_record = units[0]

    if "duid" in first_record and first_record["duid"]:
        return normalize_duid(first_record["duid"])

    return None


def get_unique_reqion(units: list) -> Optional[str]:
    if len(units) < 1:
        return None

    first_record = units[0]

    if "Region" in first_record:
        return first_record["Region"].strip()

    return None


class GeneralInformationGrouperPipeline(object):
    """
        This is the first-pass pipeline of the AEMO general information list

        It groups by clean station name

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if not "records" in item:
            raise Exception("No records found in item pipeline failed")

        generators = item["records"]

        generators = list(
            filter(lambda x: x["station_name"] != None, generators)
        )

        # sort by name

        generators_grouped = {}

        for k, v in groupby(
            generators, key=lambda v: (v["SurveyID"], v["station_name"])
        ):
            key = k[0]
            if not key in generators_grouped:
                generators_grouped[key] = []

            generators_grouped[key] += list(v)

        return {"generators": generators_grouped}


class GeneralInformationStoragePipeline(DatabaseStoreBase):
    """
        Stores the grouped General Information items from AEMO

    """

    def parse_interval(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    def process_participants(self, participants):
        s = self.session()

        for participant in participants:
            participant_name = name_normalizer(participant["Owner"])

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
                logger.info(
                    "GI: Added new partipant to NEM database: {}".format(
                        participant_name
                    )
                )

    def process_facilities(self, records):
        s = self.session()

        # Store a list of all existing duids
        all_duids = list(
            set(
                [
                    i[0]
                    for i in s.query(Facility.network_code)
                    .filter(Facility.network_code != None)
                    .all()
                ]
            )
        )

        for _, facility_records in records.items():
            facility_index = 1
            facility_station = None
            created_station = False

            station_network_name = record_get_station_name(facility_records)
            station_name = station_name_cleaner(station_network_name)

            duid_unique = has_unique_duid(facility_records)
            facility_count = len(facility_records)

            # Step 1. Find the station
            # First by duid if it's unique
            duid = get_unique_duid(facility_records)

            # all GI records should have a region
            station_network_region = get_unique_reqion(facility_records)

            # This is the most suitable unit record to use for the station
            # see helper above
            facility_station_record = get_station_record_from_facilities(
                facility_records
            )

            if duid and duid_unique and facility_count == 1:

                facility_lookup = None

                try:
                    facility_lookup = (
                        s.query(Facility)
                        .filter(Facility.network_code == duid)
                        .filter(
                            Facility.network_region == station_network_region
                        )
                        .one_or_none()
                    )
                except MultipleResultsFound:
                    logger.error(
                        "Found multiple duid for station with code {}".format(
                            duid
                        )
                    )
                    continue

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
                    .filter(Facility.network_region == station_network_region)
                    .first()
                )

                if facility_lookup and facility_lookup.station:
                    facility_station = facility_lookup.station

            if not facility_station and facility_station_join_by_name(
                station_name
            ):
                try:
                    facility_station = (
                        s.query(Station)
                        .filter(Station.name == station_name)
                        .one_or_none()
                    )
                except MultipleResultsFound:
                    logger.warning(
                        "Multiple results found for station name : {}".format(
                            station_name
                        )
                    )
                    facility_station = None

            # If we have a station name, and no duid, and it's ok to join by name
            # then find the station (make sure to region lock)
            if (
                station_name
                and not duid
                and not facility_station
                and facility_station_join_by_name(station_name)
            ):
                facility = (
                    s.query(Facility)
                    .join(Facility.station)
                    .filter(Facility.network_region == station_network_region)
                    .filter(Station.name == station_name)
                    .first()
                )

                if facility:
                    facility_station = facility.station

            # Create one as it doesn't exist
            if not facility_station:
                facility_station = Station(
                    name=station_name,
                    network_name=name_normalizer(
                        facility_station_record["station_name"]
                    ),
                    network_id="NEM",
                    created_by="pipeline.aemo.general_information",
                )

                s.add(facility_station)
                s.commit()

                created_station = True
            else:
                facility_station.updated_by = (
                    "pipeline.aemo.general_information"
                )

            for facility_record in facility_records:
                if facility_record["FuelType"] in ["Natural Gas Pipeline"]:
                    continue

                # skip these statuses too
                if facility_record["UnitStatus"] in FACILITY_INVALID_STATUS:
                    continue

                facility = None
                created_facility = False

                facility_network_name = name_normalizer(
                    facility_record["station_name"]
                )
                facility_name = station_name_cleaner(
                    facility_record["station_name"]
                )
                duid = normalize_duid(facility_record["duid"])
                reg_cap = clean_capacity(facility_record["NameCapacity"])

                units_num = facility_record["Units"] or 1
                unit_id = facility_index + (units_num - 1)

                unit = parse_unit_duid(unit_id, duid)
                unit_size = clean_capacity(facility_record["unit_capacity"])
                unit_code = get_unit_code(
                    unit, duid, facility_record["station_name"]
                )

                facility_comissioned = facility_record["SurveyEffective"]
                facility_comissioned_dt = None

                if type(facility_comissioned) is datetime:
                    facility_comissioned_dt = facility_comissioned

                try:
                    if type(facility_comissioned) is str:
                        facility_comissioned_dt = datetime.strptime(
                            facility_comissioned, "%d/%m/%y"
                        )
                except ValueError:
                    logger.error(
                        "Error parsing date: {}".format(facility_comissioned)
                    )

                facility_status = map_aemo_facility_status(
                    facility_record["UnitStatus"]
                )
                facility_network_region = normalize_aemo_region(
                    facility_record["Region"]
                )
                facility_fueltech = (
                    lookup_fueltech(
                        facility_record["FuelType"],
                        techtype=facility_record["TechType"],
                    )
                    if (
                        "FuelType" in facility_record
                        and facility_record["FuelType"]
                    )
                    else None
                )

                if not facility_fueltech:
                    logger.error(
                        "Error looking up fueltech: {} {} ".format(
                            facility_record["FuelType"],
                            facility_record["TechType"],
                        )
                    )

                # check if we have it by ocode first
                facility = (
                    s.query(Facility)
                    .filter(Facility.code == unit_code)
                    .one_or_none()
                )

                if not facility and duid:
                    try:
                        facility = (
                            s.query(Facility)
                            .filter(Facility.network_code == duid)
                            .filter(
                                Facility.network_region
                                == facility_network_region
                            )
                            # .filter(Facility.nameplate_capacity != None)
                            .one_or_none()
                        )
                    except MultipleResultsFound:
                        logger.warn(
                            "Multiple results found for duid : {}".format(duid)
                        )

                    if facility:
                        if facility.station and not facility_station:
                            facility_station = facility.station

                        logger.info(
                            "GI: Found facility by DUID: code {} station {}".format(
                                facility.code,
                                facility.station.name
                                if facility.station
                                else None,
                            )
                        )

                # Done trying to find existing
                if not facility:
                    facility = Facility(
                        code=unit_code,
                        network_code=duid,
                        created_by="pipeline.aemo.general_information",
                    )
                    facility.station = facility_station

                    created_facility = True

                if duid and not facility.network_code:
                    facility.network_code = duid
                    facility.updated_by = "pipeline.aemo.general_information"

                if not facility.network_region:
                    facility.network_region = facility_network_region
                    facility.updated_by = "pipeline.aemo.general_information"

                if not facility.network_name:
                    facility.network_name = facility_network_name
                    facility.updated_by = "pipeline.aemo.general_information"

                if not facility.fueltech_id and facility_fueltech:
                    facility.fueltech_id = facility_fueltech
                    facility.updated_by = "pipeline.aemo.general_information"

                if not facility.capacity_registered or (
                    facility.status and facility.status != "operating"
                ):
                    facility.capacity_registered = reg_cap
                    facility.updated_by = "pipeline.aemo.general_information"

                # @TODO work this out
                # facility.dispatch_type = facility_dispatch_type

                if not facility.unit_id:
                    facility.unit_id = unit.id
                    facility.unit_number = unit.number
                    facility.unit_size = unit_size
                    facility.unit_alias = unit.alias

                if not facility.unit_capacity or (
                    facility.status and facility.status != "operating"
                ):
                    facility.unit_capacity = unit_size
                    facility.updated_by = "pipeline.aemo.general_information"

                # if not facility.status_id:
                facility.status_id = facility_status
                # facility.updated_by = "pipeline.aemo.general_information"

                if not facility.registered and facility_comissioned_dt:
                    facility.registered = facility_comissioned_dt
                    facility.updated_by = "pipeline.aemo.general_information"

                facility.station = facility_station

                if facility.fueltech_id is None:
                    logger.warning(
                        "Could not find fueltech for: {} {}".format(
                            facility.code, facility.network_code
                        )
                    )

                # facility.status_id = facility_status

                if facility_station and not facility.station:
                    facility.station = facility_station

                if facility.status_id is None:
                    raise Exception(
                        "GI: Failed to map status ({}) on row: {}".format(
                            facility.status_id, facility_record
                        )
                    )

                s.add(facility)
                s.commit()

                facility_index += units_num

                if created_station:
                    logger.info(
                        "GI: {} station with name {} ".format(
                            "Created" if created_station else "Updated",
                            station_name,
                            # facility_station.id,
                        )
                    )

                if created_facility:
                    logger.info(
                        "GI: {} facility with duid {} to station {}".format(
                            "Created" if created_facility else "Updated",
                            duid,
                            station_name,
                        )
                    )

        try:
            s.commit()
        except Exception as e:
            logger.error(e)
            raise e
        finally:
            s.close()

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        if not "generators" in item and type(item["generators"]) is not list:
            raise Exception("Invalid item - no generators located")

        generators = item["generators"]

        self.process_facilities(generators)
