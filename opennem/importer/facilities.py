""" " OpenNEM Facility and Station Importer"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from opennem.core.dispatch_type import DispatchType
from opennem.core.loader import load_data
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Location, Station
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


async def import_station_set(stations: StationSet, only_insert_facilities: bool = False) -> None:
    async with SessionLocal() as session:
        for station in stations:
            if not station.code:
                logger.error(f"Skipping station: {station.code} - {station.name} (network name: {station.network_name})")
                continue

            async with session.begin():
                # Fetch station with eager-loaded facilities
                station_query = select(Station).options(selectinload(Station.facilities)).where(Station.code == station.code)
                station_result = await session.execute(station_query)
                station_model = station_result.scalar_one_or_none()

                if not station_model:
                    station_model = Station(code=station.code, created_by="opennem.importer.facilities")
                    logger.debug(f"Adding station: {station.code} - {station.name} (network name: {station.network_name})")
                else:
                    logger.debug(f"Updating station: {station.code} - {station.name} (network name: {station.network_name})")

                # Update station details
                station_model.name = station.name
                station_model.network_name = station.network_name
                station_model.description = station.description
                station_model.approved = station.approved
                station_model.website_url = station.website_url

                if station.approved:
                    station_model.approved_at = datetime.now()
                    station_model.approved_by = "opennem.importer.facilities"
                else:
                    station_model.approved_at = None
                    station_model.approved_by = None

                if not station_model.location_id:
                    station_model.location = Location()

                if station.location:
                    station_model.location.locality = station.location.locality
                    station_model.location.state = station.location.state
                    station_model.location.postcode = station.location.postcode
                    station_model.location.country = station.location.country

                if station.location.lat and station.location.lng:
                    station_model.location.geom = f"SRID=4326;POINT({station.location.lng} {station.location.lat})"

                session.add(station_model)
                await session.flush()

                # Process facilities
                existing_facilities = {(f.code, f.network_id): f for f in station_model.facilities}

                for fac in station.facilities:
                    facility_key = (fac.code, fac.network_id)
                    if facility_key in existing_facilities:
                        if only_insert_facilities:
                            logger.debug(f" => skip updating facility {fac.code}")
                            continue
                        facility_model = existing_facilities[facility_key]
                        logger.debug(f" => Updating existing facility {fac.code} in {station_model.code}")
                    else:
                        facility_model = Facility(code=fac.code, network_id=fac.network_id)
                        logger.debug(f" => Adding new facility {fac.code} to {station_model.code}")

                    # Update facility details
                    facility_model.fueltech_id = fac.fueltech_id
                    facility_model.status_id = fac.status_id
                    facility_model.dispatch_type = fac.dispatch_type
                    facility_model.capacity_registered = fac.capacity_registered
                    facility_model.registered = fac.registered
                    facility_model.network_region = fac.network_region
                    facility_model.unit_id = fac.unit_id
                    facility_model.unit_number = fac.unit_number
                    facility_model.unit_alias = fac.unit_alias
                    facility_model.unit_capacity = fac.unit_capacity
                    facility_model.emissions_factor_co2 = fac.emissions_factor_co2 or 0.0
                    facility_model.emission_factor_source = fac.emission_factor_source
                    facility_model.approved = fac.approved
                    facility_model.approved_by = "opennem.importer" if fac.approved else None

                    if not facility_model.created_by:
                        facility_model.created_by = "opennem.init"

                    if facility_model not in station_model.facilities:
                        station_model.facilities.append(facility_model)

                    session.add(facility_model)

                await session.flush()

            await session.commit()


async def import_facilities() -> None:
    station_data = load_data("stations.json", from_project=True)
    stations = StationSet()

    for s in station_data:
        stations.add_dict(s)

    await import_station_set(stations)


if __name__ == "__main__":
    import asyncio

    asyncio.run(import_facilities())
