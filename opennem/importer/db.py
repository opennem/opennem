import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from opennem.core.loader import load_data
from opennem.core.normalizers import station_name_cleaner
from opennem.core.stats.store import init_stats
from opennem.db import SessionLocal
from opennem.db.load_fixtures import load_fixtures
from opennem.db.models.opennem import Facility, Location, Station
from opennem.importer.emissions import import_emissions_csv
from opennem.importer.fueltechs import init_fueltechs
from opennem.importer.interconnectors import import_nem_interconnects
from opennem.importer.osm import init_osm
from opennem.importer.photos import import_photos_from_fixtures
from opennem.importer.registry import registry_import
from opennem.importer.rooftop import rooftop_facilities
from opennem.importer.wikidata import wikidata_join_mapping, wikidata_photos
from opennem.schema.stations import StationSet
from opennem.workers.facility_data_ranges import update_facility_seen_range

logger = logging.getLogger(__name__)
s = SessionLocal()


def registry_init() -> None:
    registry = registry_import()
    session = SessionLocal()

    for station in registry:
        station_dict = station.dict(exclude={"id"})

        station_model = session.query(Station).filter_by(code=station.code).one_or_none()

        if not station_model:
            # pylint:disable no-member
            main_dict = {
                i: k
                for i, k in station_dict.items()
                if i not in ["facilities", "location", "participant", "photos", "network"]
            }

            main_dict["facilities"] = []
            main_dict["location"] = None

            station_model = Station(**main_dict)
            station_model.approved = True
            station_model.approved_at = datetime.now()
            station_model.approved_by = "opennem.registry"
            station_model.created_by = "opennem.registry"

        # location
        if not station_model.location_id:
            location_dict = {
                i: k
                for i, k in station_dict["location"].items()
                if i not in ["id", "weather_station", "weather_nearest", "country", "lat", "lng"]
            }
            station_model.location = Location(**location_dict)

        if station.location.lat and station.location.lng:
            station_model.location.geom = "SRID=4326;POINT({} {})".format(
                station.location.lng, station.location.lat
            )

        # clean station name
        if station.name:
            station_model.name = station_name_cleaner(station.network_name)

        if station.network_name:
            station_model.name = station_name_cleaner(station.network_name)

        session.add(station_model)
        session.commit()

        for fac in station.facilities:
            f = (
                session.query(Facility)
                .filter_by(code=fac.code)
                .filter_by(network_id=fac.network.code)
                .one_or_none()
            )

            if not f:
                logger.info("Added facility {} {}".format(fac.code, fac.network.code))

                f = Facility(
                    **{
                        i: k
                        for i, k in fac.dict().items()
                        if i
                        not in [
                            "id",
                            "fueltech",
                            "status",
                            "network",
                            "revision_ids",
                            "scada_power",
                        ]
                    }
                )
                f.approved_by = "opennem.registry"
                f.created_by = "opennem.registry"
                f.approved_at = datetime.now()
                f.created_at = datetime.now()

            f.network_id = fac.network.code

            if fac.fueltech:
                f.fueltech_id = fac.fueltech.code

            if fac.network.code:
                f.network_code = fac.network.code

            f.status_id = fac.status.code

            f.approved = True

            if station_model.id:
                f.station_id = station_model.id
            else:
                station_model.facilities.append(f)
                session.add(station_model)

            session.add(f)

        try:
            session.commit()
        except IntegrityError as e:
            logger.error(e)


def opennem_init() -> None:
    station_data = load_data("opennem_stations.json", from_project=True)
    stations = StationSet()

    for s in station_data:
        stations.add_dict(s)

    import_station_set(stations)


def mms_init() -> None:
    station_data = load_data("mms_stations.json", from_project=True)
    stations = StationSet()

    for s in station_data:
        stations.add_dict(s)

    import_station_set(stations)


def import_station_set(stations: StationSet, only_insert_facilities: bool = False) -> None:
    session = SessionLocal()

    for station in stations:
        add_or_update: str = "Updating"

        station_model = (
            session.query(Station)
            # .outerjoin(Station.facilities)
            # .outerjoin(Station.location)
            # .outerjoin(Facility.fueltech)
            .filter_by(code=station.code).one_or_none()
        )

        if not station_model:
            add_or_update = "Adding"
            station_model = Station(code=station.code)
            station_model.created_by = "opennem.init"

        logger.debug("{} station: {}".format(add_or_update, station.code))

        if station.description:
            station_model.description = station.description

        if station.name:
            station_model.name = station_name_cleaner(station.name)

        if station.network_name:
            station_model.name = station_name_cleaner(station.network_name)

        station_model.approved = station.approved

        if station.approved:
            station_model.approved = True
            station_model.approved_at = datetime.now()
            station_model.approved_by = "opennem.init"
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
            station_model.location.locality = station.location.locality
            station_model.location.state = station.location.state
            station_model.location.postcode = station.location.postcode
            station_model.location.country = station.location.country

        if station.location.lat and station.location.lng:
            station_model.location.geom = "SRID=4326;POINT({} {})".format(
                station.location.lng, station.location.lat
            )

        session.add(station_model)
        session.commit()

        for fac in station.facilities:
            facility_added = False

            facility_model = (
                session.query(Facility)
                .filter_by(code=fac.code)
                .filter_by(network_id=fac.network.code)
                .one_or_none()
            )

            if facility_model and only_insert_facilities:
                logger.debug(" => skip updating {}".format(facility_model.code))
                continue

            if not facility_model:
                facility_model = Facility(code=fac.code, network_id=fac.network.code)
                facility_added = True

            if facility_model.station_id != station_model.id:
                facility_model.station_id = station_model.id
                logger.debug(
                    " => Reassigned facility {} to station {}".format(
                        facility_model.code, station_model.code
                    )
                )

            # fueltech
            if fac.fueltech:
                facility_model.fueltech_id = fac.fueltech.code

            if fac.fueltech_id:
                facility_model.fueltech_id = fac.fueltech_id

            # network
            if fac.network:
                facility_model.network_id = fac.network.code

            if fac.network_id:
                facility_model.network_id = fac.network_id

            # status
            if fac.status:
                facility_model.status_id = fac.status.code

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


def import_facilities() -> None:
    registry_init()
    logger.info("Registry initialized")

    opennem_init()
    logger.info("Opennem stations imported")

    mms_init()
    logger.info("MMS stations imported")

    rooftop_facilities()
    logger.info("Rooftop stations initialized")


def init() -> None:
    """
    These are all the init steps required after a db has been initialized
    """
    load_fixtures()
    logger.info("Fixtures loaded")

    import_facilities()

    import_emissions_csv()
    logger.info("Emission data initialized")

    init_fueltechs()
    logger.info("Initialized fueltechs")

    import_nem_interconnects()
    logger.info("Initialized interconnectors")

    wikidata_join_mapping()
    logger.info("Imported wikidata for stations")

    wikidata_photos()
    logger.info("Imported wikidata photos")

    import_photos_from_fixtures()
    logger.info("Imported photos from wikidata")

    init_osm()
    logger.info("Initialized osm")

    init_stats()
    logger.info("Stats data initialized")

    update_facility_seen_range()
    logger.info("Ran seen range")
