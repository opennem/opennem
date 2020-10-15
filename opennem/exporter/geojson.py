from opennem.api.geo.router import geo_facilities_api
from opennem.db import SessionLocal
from opennem.exporter.aws import write_to_s3


def export_facility_geojson():
    session = SessionLocal()

    facility_geo = geo_facilities_api(only_approved=True, session=session)

    write_to_s3("geo/au_facilities.json", facility_geo.json())


if __name__ == "__main__":
    export_facility_geojson()
