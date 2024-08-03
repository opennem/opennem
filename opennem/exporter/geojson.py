import asyncio
import logging

from opennem.api.geo.controllers import stations_to_geojson
from opennem.api.station.controllers import get_stations
from opennem.exporter.aws import write_to_s3

logger = logging.getLogger("opennem.exporter.geojson")


async def export_facility_geojson() -> None:
    """Get the GeoJSON for facilities and write it to S3"""
    stations = await get_stations()

    logger.info(f"Found {len(stations)} stations")

    if not stations:
        raise Exception("No stations found")

    stations_geo = await stations_to_geojson(stations)

    write_to_s3(stations_geo.model_dump_json(exclude_unset=True), "/v3/geo/au_facilities.json")


if __name__ == "__main__":
    asyncio.run(export_facility_geojson())
