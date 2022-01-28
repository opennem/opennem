import csv
import logging
from pathlib import Path
from typing import List

from opennem.core.loader import load_data
from opennem.core.parsers.osm import get_osm_geom
from opennem.db import SessionLocal
from opennem.db.models.opennem import Location, Station
from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.importer.osm")

CSV_IMPORT_FORMAT_COLUMNS = [
    "network_id",
    "station_code",
    "osm_way_id",
]


class OSMImportCSVSchema(BaseConfig):
    """Defines a schema for osm way imports"""

    network_id: str
    station_code: str
    osm_way_id: str


def get_import_osm_data(file_name: str = "osm_ways.csv") -> List[OSMImportCSVSchema]:
    osm_ways_path: Path = load_data(file_name, from_project=True, return_path=True)

    if not osm_ways_path.is_file():
        raise Exception("Could not import photo file data: {}".format(str(osm_ways_path)))

    osm_way_records: List[OSMImportCSVSchema] = []

    with osm_ways_path.open() as fh:
        # skip csv header
        fh.readline()

        csvreader = csv.DictReader(fh, fieldnames=CSV_IMPORT_FORMAT_COLUMNS)

        # Parse CSV records into schemas
        osm_way_records = [OSMImportCSVSchema(**i) for i in csvreader]

    return osm_way_records


def import_osm_way_data() -> None:
    """Updates the OSM way ids for stations from the CSV file fixture"""
    session = SessionLocal()
    station_osm_records = get_import_osm_data()

    for station_osm_record in station_osm_records:
        station = (
            session.query(Station)
            .filter(Station.code == station_osm_record.station_code)
            .one_or_none()
        )

        if not station:
            logger.error("Could not find station {}".format(station_osm_record.station_code))
            continue

        if not station.location:
            logger.error(
                "Station {} does not have a location".format(station_osm_record.station_code)
            )
            continue

        station.location.osm_way_id = station_osm_record.osm_way_id
        session.add(station)
        session.commit()

        logger.info("Updated station: {}".format(station.code))


def import_osm_ways() -> int:
    """Gets the geometries for each OSM way id and store them against the station geom"""
    session = SessionLocal()

    stations_with_ways = (
        session.query(Station).join(Location).filter(Location.osm_way_id.isnot(None)).all()
    )

    if not stations_with_ways or len(stations_with_ways) < 1:
        logger.error("No stations with ways!")
        return 0

    station_count = 0

    for station in stations_with_ways:

        location: Location = station.location

        geom_boundary = None

        try:
            geom_boundary = get_osm_geom(station.location.osm_way_id)
        except Exception as e:
            logger.error("get osm wkt error: {}".format(e))
            pass

        if not geom_boundary:
            logger.error("Error getting WKT from OSM")
            continue

        location.boundary = geom_boundary
        session.add(location)
        session.commit()

        logger.info("Updated boundary geom from OSM for station: {}".format(station.code))

    return station_count


def init_osm() -> None:
    import_osm_way_data()
    import_osm_ways()


if __name__ == "__main__":
    init_osm()
