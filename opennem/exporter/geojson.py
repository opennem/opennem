import asyncio

from opennem.api.geo.router import geo_facilities_api
from opennem.db import SessionLocal
from opennem.exporter.aws import write_to_s3


async def export_facility_geojson() -> None:
    """Get the GeoJSON for facilities and write it to S3"""
    async with SessionLocal() as session:
        facility_geo = await geo_facilities_api(only_approved=True, session=session)

    write_to_s3(facility_geo.model_dump_json(exclude_unset=True), "/v3/geo/au_facilities.json")


if __name__ == "__main__":
    asyncio.run(export_facility_geojson())
