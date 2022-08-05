"""" OpenNEM Facility and Station Importer """
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from opennem.core.dispatch_type import DispatchType
from opennem.core.loader import load_data
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Location, Station
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.schema.stations import StationSet

logger = logging.getLogger("opennem.importer.facilities")


@dataclass
class ParticipantSchema:
    code: str
    name: str
    network_name: str | None
    network_code: str | None
    country: str | None
    abn: str | None


@dataclass
class LocationSchema:
    address1: str | None
    address2: str | None
    locality: str | None
    state: str | None
    postcode: str | None
    country: str | None

    geocode_processed_at: datetime | None
    lat: float | None
    lng: float | None
    osm_way_id: str | None
    place_id: str | None

    geocode_by: str | None
    geocode_approved: bool = False
    geocode_skip: bool = False


@dataclass
class FacilitySchema:
    network_id: str
    fueltech_id: str | None
    status_id: str | None

    # @TODO no longer optional
    code: str | None
    network_code: str | None
    network_region: str | None
    network_name: str | None

    dispatch_type: DispatchType

    interconnector: bool
    interconnector_region_to: str | None
    interconnector_region_from: str | None

    capacity_registered: float | None
    expected_closure_date: datetime | None
    expected_closure_year: int | None

    registered: datetime | None
    deregistered: datetime | None

    unit_id: int | None
    unit_number: int | None
    unit_alias: str | None
    unit_capacity: float | None

    emissions_factor_co2: float | None


@dataclass
class StationSchema:
    # participant_id: int | None
    # location_id: int | None

    code: str
    name: str
    network_name: str | None
    description: str | None

    wikipedia_link: str | None
    wikidata_id: str | None
    website_url: str | None

    approved: bool
    approved_by: str | None

    facilities: list[FacilitySchema] | None
    location: LocationSchema | None
    # participant: ParticipantSchema | None


ALL_DB_REMOVE = [
    "id",
    "_sa_instance_state",
    "updated_at",
    "created_at",
    "created_by",
]

STATION_DB_KEYS_REMOVE = [
    "approved_at",
    "photos",
    "network_code",
    "location",
    "facilities",
    "participant_id",
    "location_id",
]


LOCATION_DB_KEYS_REMOVE = ["geom", "boundary"]

FACILITY_DB_KEYS_REMOVE = [
    "station_id",
    "network",
    "fueltech",
    "status",
    "data_first_seen",
    "data_last_seen",
    "approved",
    "approved_at",
    "approved_by",
    "active",
]


def _remove_keys(dict: dict, remove_from: list[str]) -> dict:
    """Remove keys from dict"""

    for key in remove_from:
        if key in dict:
            del dict[key]

    return dict


def clean_station_model_keys(station_dict: dict[str, Any]) -> dict[str, Any]:
    """Cleans up a station dict from the database"""
    station_dict = station_dict.copy()

    station_dict = _remove_keys(station_dict, ALL_DB_REMOVE)
    station_dict = _remove_keys(station_dict, STATION_DB_KEYS_REMOVE)

    return station_dict


def clean_location_model_keys(location_dict: dict[str, Any]) -> dict[str, Any]:
    """Cleans up a location dict from the database"""
    location_dict = location_dict.copy()

    location_dict = _remove_keys(location_dict, ALL_DB_REMOVE)
    location_dict = _remove_keys(location_dict, LOCATION_DB_KEYS_REMOVE)

    return location_dict


def clean_facility_model_keys(facility_dict: dict[str, Any]) -> dict[str, Any]:
    """Cleans up a station dict from the database"""
    facility_dict = facility_dict.copy()

    facility_dict = _remove_keys(facility_dict, ALL_DB_REMOVE)
    facility_dict = _remove_keys(facility_dict, FACILITY_DB_KEYS_REMOVE)

    return facility_dict


def import_station_set(stations: StationSet, only_insert_facilities: bool = False) -> None:
    session = SessionLocal()

    for station in stations:
        add_or_update: str = "Updating"

        station_model = session.query(Station).filter_by(code=station.code).one_or_none()

        if not station_model:
            add_or_update = "Adding"
            station_model = Station(code=station.code)
            station_model.created_by = "opennem.importer.facilities"

        logger.debug(
            "{} station: {} - {} (network name: {})".format(
                add_or_update, station.code, station.name, station.network_name
            )
        )

        if station.description:
            station_model.description = station.description

        if station.name:
            station_model.name = station.name

        if station.network_name:
            station_model.network_name = station.network_name

        station_model.approved = station.approved

        if station.approved:
            station_model.approved = True
            station_model.approved_at = datetime.now()
            station_model.approved_by = "opennem.importer.facilities"
        else:
            station_model.approved_at = None
            station_model.approved_by = None

        if station.website_url:
            station_model.website_url = station.website_url

        if station.network_name:
            station_model.network_name = station.network_name

        if not station_model.location_id:
            station_model.location = Location()

        if station.location:
            # location_model = (
            #     session.query(Location)
            #     .filter(Location. == station.location.postcode)
            #     .filter(Location.postcode == station.location.postcode)
            #     .filter(Location.locality == station.location.locality)
            #     .filter(Location.state == station.location.state)
            #     .one_or_none()
            # )
            station_model.location.locality = station.location.locality
            station_model.location.state = station.location.state
            station_model.location.postcode = station.location.postcode
            station_model.location.country = station.location.country

        if station.location.lat and station.location.lng:
            station_model.location.geom = "SRID=4326;POINT({} {})".format(station.location.lng, station.location.lat)

        session.add(station_model)
        session.commit()

        for fac in station.facilities:
            facility_added = False

            facility_model = (
                session.query(Facility).filter_by(code=fac.code).filter_by(network_id=fac.network_id).one_or_none()
            )

            if facility_model and only_insert_facilities:
                logger.debug(" => skip updating {}".format(facility_model.code))
                continue

            if not facility_model:
                logger.debug(f" => no facility for {fac.code} and {fac.network_id}")
                facility_model = Facility(code=fac.code, network_id=fac.network.code)
                facility_added = True

            # if facility_model.station_id != station_model.id:
            # facility_model.station_id = station_model.id
            # logger.debug(" => Reassigned facility {} to station {}".format(facility_model.code, station_model.code))

            # fueltech
            if fac.fueltech_id:
                facility_model.fueltech_id = fac.fueltech_id

            # network
            if fac.network_id:
                facility_model.network_id = fac.network_id

            # status
            if fac.status_id:
                facility_model.status_id = fac.status_id

            # rest
            if fac.dispatch_type:
                facility_model.dispatch_type = fac.dispatch_type

            if fac.capacity_registered:
                facility_model.capacity_registered = fac.capacity_registered

            if fac.registered:
                facility_model.registered = fac.registered

            if fac.network_region:
                facility_model.network_region = fac.network_region

            facility_model.unit_id = fac.unit_id
            facility_model.unit_number = fac.unit_number
            facility_model.unit_alias = fac.unit_alias
            facility_model.unit_capacity = fac.unit_capacity

            if fac.emissions_factor_co2:
                facility_model.emissions_factor_co2 = fac.emissions_factor_co2

            if fac.approved:
                facility_model.approved = fac.approved

            if fac.approved:
                facility_model.approved_by = "opennem.importer"
            else:
                facility_model.approved_by = None

            if not facility_model.created_by:
                facility_model.created_by = "opennem.init"

            session.add(facility_model)
            station_model.facilities.append(facility_model)
            logger.debug(
                " => {} facility {} to {} {}".format(
                    "Added" if facility_added else "Updated",
                    fac.code,
                    facility_model.network_id,
                    facility_model.network_region,
                )
            )

        session.add(station_model)
        session.commit()


def dump_facilities() -> None:
    """Dump facilities to JSON"""

    station_map = []

    with SessionLocal() as sess:
        stations = (
            sess.query(Station)
            .join(Facility, Location)
            .filter(Facility.network_id.in_(["NEM", "WEM"]))
            .order_by(Facility.network_id, Facility.network_region, Station.code)
            .all()
        )

        logger.debug(f"Got {len(stations)} stations")

        for station in stations:
            station_dict = clean_station_model_keys(station.__dict__)
            station_dict["facilities"] = []
            station_dict["location"] = None

            if station.location:
                location_dict = clean_location_model_keys(station.location.__dict__)

                # @NOTE hardcoded as it's WEM/NEM for now
                location_dict["country"] = "AU"

                # @NOTE lat and lng set as they're props
                location_dict["lat"] = None
                location_dict["lng"] = None

                if station.location.lat:
                    location_dict["lat"] = station.location.lat

                if station.location.lng:
                    location_dict["lng"] = station.location.lng

                location_model = LocationSchema(**location_dict)
                station_dict["location"] = location_model

            for facility in station.facilities:
                logger.debug(f"{facility.network.code} - Station {station.name} - {facility.code}")
                facility_model = FacilitySchema(**clean_facility_model_keys(facility.__dict__))
                station_dict["facilities"].append(facility_model)

            station_model = StationSchema(**station_dict)
            # print(station.code)

            station_map.append(station_model)

        with open("stations.json", "w+") as fh:
            # fh.write()
            json.dump(station_map, fh, cls=OpenNEMJSONEncoder, indent=4)


def import_facilities() -> None:
    station_data = load_data("stations.json", from_project=True)
    stations = StationSet()

    for s in station_data:
        stations.add_dict(s)

    import_station_set(stations)


if __name__ == "__main__":
    import_facilities()
    # dump_facilities()
