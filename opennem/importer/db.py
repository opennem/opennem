import logging
import re
from datetime import datetime
from pprint import pprint
from typing import List, Optional, Union

from dictalchemy.utils import fromdict
from pydantic import BaseModel
from sqlalchemy.orm.exc import MultipleResultsFound

# from opennem.core.loader import load_data
from opennem.db import SessionLocal
from opennem.db.load_fixtures import load_fixtures
from opennem.db.models.opennem import Facility, Location, Revision, Station
from opennem.importer.aemo_gi import gi_import
from opennem.importer.aemo_rel import rel_import
from opennem.importer.mms import mms_import
from opennem.importer.registry import registry_import

from .comparator import compare_record_differs

logger = logging.getLogger(__name__)
s = SessionLocal()


def load_revisions(stations):
    pass


def create_revision(model):
    # s = session()

    # make_transient(model)

    clone = model.asdict(exclude_pk=True)
    # clone.pop("id")
    # model.fromdict(clone)

    # pylint: disable=no-member
    clone_model = Station().fromdict(clone)

    return clone_model


def get_schema_name(record: object) -> str:
    class_name = str(record.__class__.__name__)

    class_name = re.sub("Schema", "", class_name)

    class_name = class_name.lower()

    return class_name


def revision_factory_join_field(record_instance: BaseModel) -> str:
    class_name = str(record_instance.__class__.__name__)

    FIELD_MAP = {
        "StationSchema": "station_id",
        "FacilitySchema": "facility_id",
        "LocationSchema": "location_id",
    }

    if class_name in FIELD_MAP.keys():
        return FIELD_MAP[class_name]

    raise Exception("Could not map record %s", record_instance)


def revision_factory(
    record: BaseModel, field_names: Union[str, List[str]], created_by: str,
) -> Optional[Revision]:

    if isinstance(field_names, str):
        field_names = [field_names]

    revision_data = {}

    for field_name in field_names:
        # field_type = get_schema_name(record)
        field_value = getattr(record, field_name)

        if isinstance(field_value, BaseModel):
            _value_dict = field_value.dict()

            # we only store the primary keys in associations rather
            # than the full record.
            if "id" in _value_dict:
                field_value = _value_dict["id"]

            elif "code" in _value_dict:
                field_value = _value_dict["code"]

            else:
                logger.error("Could not serialize data value %s", field_value)
                field_value = False

        if field_value is not False:
            revision_data[field_name] = field_value

    if not record.id:
        logger.error("Require a code to create a revision: %s", record)
        return None

    if len(revision_data.keys()) < 1:
        logger.error("Require data to lookup for code %s", record.code)
        return None

    column_name = revision_factory_join_field(record)

    __query = (
        s.query(Revision).filter(getattr(Revision, column_name) == record.id)
        # .filter(Revision.code == record.code)
    )

    for data_name, data_value in revision_data.items():
        if isinstance(data_value, str):
            __query = __query.filter(
                Revision.changes[data_name].as_string() == data_value
            )
        if isinstance(data_value, bool):
            __query = __query.filter(
                Revision.changes[data_name].as_boolean() == data_value
            )
        if isinstance(data_value, int):
            __query = __query.filter(
                Revision.changes[data_name].as_integer() == data_value
            )
        if isinstance(data_value, float):
            __query = __query.filter(
                Revision.changes[data_name].as_float() == data_value
            )

    revision_lookup = None

    try:
        revision_lookup = __query.one_or_none()
    except MultipleResultsFound:
        logger.info(
            "Revision exists: %s %s %s", record.code, field_name, field_value,
        )
        return None

    if revision_lookup:
        return None

    revision = Revision(created_by=created_by, changes=revision_data,)

    # s.add(revision)
    # s.commit()

    return revision


def load_revision(records, created_by):
    logger.info("Running db test")

    for station_record in records:
        station_model = (
            s.query(Station)
            .filter(Station.code == station_record.code)
            .one_or_none()
        )

        if not station_model:
            logger.info(
                f"New station {station_record.name} {station_record.code}"
            )

            station_dict = station_record.dict(
                include={"code", "network_name", "name", "location"}
            )
            # pprint(station_dict)

            # pylint:disable no-member
            station_model = fromdict(Station(), station_dict)
            station_model.approved = False
            station_model.created_by = created_by

            # location
            if "location" in station_dict and station_dict["location"]:
                station_model.location = fromdict(
                    Location(), station_dict["location"], exclude=["id"]
                )

                if station_record.location.lat and station_record.location.lng:
                    station_model.location.geom = station_record.location.geom

            s.add(station_model)
            s.commit()

            station_record.id = station_model.id

            # revision = revision_factory(
            #     station_record, ["code", "name", "network_name"], created_by,
            # )

            # if revision:
            #     station_model.revisions.append(revision)

            # s.add(station_model)
            # s.commit()

        else:
            for field in ["name"]:
                if getattr(station_model, field) != getattr(
                    station_record, field
                ):
                    revision_factory(station_record, field, created_by)

        for facility in station_record.facilities:
            facility_model = (
                s.query(Facility)
                .filter(Facility.code == facility.code)
                .first()
            )

            if not facility_model:
                logger.info(
                    "New facility %s => %s", station_record.name, facility.code
                )

                facility_dict = facility.dict(
                    include={
                        "code",
                        "network",
                        # "network_id",
                        "dispatch_type",
                        "station",
                        # "station_id",
                        # "status",
                        "network_code",
                        "network_region",
                        "network_name",
                    }
                )
                # pprint(station_dict)

                # pylint:disable no-member
                facility_model = fromdict(Facility(), facility_dict)
                facility_model.network_id = facility.network.code
                facility_model.approved = False
                facility_model.created_by = created_by

                s.add(facility_model)
                s.commit()

                facility.id = facility_model.id

                # @NOTE don't create revisions for new facilities
                # revision = revision_factory(
                #     facility, ["code", "dispatch_type"], created_by
                # )

                # if revision:
                #     facility_model.revisions.append(revision)

                # s.add(facility_model)
                # s.commit()

            else:
                facility.id = facility_model.id

            for field in [
                "fueltech",
                "status",
                "capacity_registered",
            ]:
                revision = None

                if compare_record_differs(facility_model, facility, field):
                    # logger.info(
                    #     "%s and %s differ",
                    #     getattr(facility, field),
                    #     getattr(facility_model, field),
                    # )

                    revision = revision_factory(facility, field, created_by)

                if revision:
                    facility_model.revisions.append(revision)

            s.add(facility_model)

            station_model.facilities.append(facility_model)
            s.add(station_model)
            s.commit()


def db_test():
    s.query(Revision).delete()

    mms = mms_import()
    rel = rel_import()
    gi = gi_import()

    load_revision(mms, "aemo.mms.202006")
    load_revision(rel, "aemo.rel.2020006")
    load_revision(gi, "aemo.gi.202006")


def registry_init():
    registry = registry_import()

    for station in registry:
        station_dict = station.dict(exclude={"id"})
        # pprint(station_dict)

        # pylint:disable no-member
        station_model = fromdict(Station(), station_dict)
        station_model.approved = True
        station_model.approved_at = datetime.now()
        station_model.approved_by = "opennem.registry"
        station_model.created_by = "opennem.registry"

        # location
        station_model.location = fromdict(
            Location(), station_dict["location"], exclude=["id"],
        )

        if station.location.lat and station.location.lng:
            station_model.location.geom = "SRID=4326;POINT({} {})".format(
                station.location.lng, station.location.lat
            )

        for fac in station.facilities:
            f = Facility(
                **fac.dict(
                    exclude={
                        "id",
                        "fueltech",
                        "status",
                        "network",
                        "revision_ids",
                        "scada_power",
                    }
                )
            )

            f.network_id = fac.network.code

            if fac.fueltech:
                f.fueltech_id = fac.fueltech.code

            f.status_id = fac.status.code

            f.approved = True
            f.approved_by = "opennem.registry"
            f.created_by = "opennem.registry"
            f.approved_at = datetime.now()
            f.created_at = datetime.now()

            station_model.facilities.append(f)

        s.add(station_model)

    s.commit()


def test_revisions():
    registry = registry_import()
    # mms = mms_import()

    k = registry.get_code("KWINANA")

    station = Station(code=k.code, name=k.name, network_name=k.network_name,)
    s.add(station)
    s.commit()

    # pylint: disable=no-member
    station_clone = station.asdict()
    station_clone.pop("id")

    pprint(station_clone)

    station = create_revision(station)

    station.location = Location(
        address1=k.location.address1,
        address2=k.location.address2,
        locality=k.location.locality,
        state=k.location.state,
        postcode=k.location.postcode,
    )

    s.add(station)
    s.commit()

    station = create_revision(station)

    station.name = "Kwinana Edited"

    s.add(station)
    s.commit()


def init():
    load_fixtures()
    logger.info("Fixture loaded")

    registry_init()
    logger.info("Registry initialized")

