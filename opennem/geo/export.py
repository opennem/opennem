import decimal
import json
from datetime import date, datetime
from decimal import Decimal
from pprint import pprint

from geojson import Feature, FeatureCollection, Point, dumps
from smart_open import open
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import metadata

engine = db_connect()
session = sessionmaker(bind=engine)


UPLOAD_ARGS = {
    "ContentType": "application/json",
}


def wem_export():

    __sql = """
        select
            wf.code as duid,
            wf.capacity_maximum,
            wf.comissioned,
            wf.name as duid_name,
            ws.name,
            wf.fueltech_id as fueltech,
            f.label as fueltech_label,
            wf.status_id as status,
            fs.label as status_label,
            ws.code as station_code,
            ws.boundary as station_boundary,
            ST_AsGeoJSON(ws.geom) as station_point,
            ws.state,
            ws.postcode,
            ST_X(ws.geom),
            ST_Y(ws.geom),
            ST_AsText(ws.geom),
            wf.id,
            ws.id
        from wem_station ws
        right join wem_facility wf on wf.station_id = ws.id
        join fueltech f on f.code = wf.fueltech_id
        join facility_status fs on fs.code = wf.status_id
        order by station_code asc
        --join wem_facility_scada wfs on wfs.facility_id = wf.id
    """

    query = __sql.format()
    features = []
    current_name = None
    current_station_code = None
    f = None

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:
            name = row[4] or row[3]
            station_id = row[18]

            if current_station_code != station_id:
                if f is not None:
                    features.append(f)

                f = Feature()
                current_station_code = station_id

                if row[11]:
                    f.geometry = Point((row[15], row[14]))

                f.properties = {
                    "oid": "wem_{}".format(row[17]),
                    "station_id": row[0],
                    "station_code": row[9],
                    "facility_id": row[0],
                    "network": "WEM",
                    "network_region": "WA",
                    "state": row[12],
                    "postcode": row[13],
                    "name": name,
                    "duid_data": [],
                }

            f.properties["duid_data"].append(
                {
                    "duid": row[0],
                    "comissioned_date": row[2].isoformat()
                    if type(row[2]) is datetime
                    else str(row[2]),
                    "fuel_tech": row[5],
                    "fuel_tech_label": row[6],
                    "status": row[7],
                    "status_label": row[8],
                    "registered_capacity": float(row[1]),
                }
            )

    if f:
        features.append(f)

    return features


def nem_export():
    __sql = """
        select
            wf.code as duid,
            wf.nameplate_capacity,
            wf.registered,
            wf.name as duid_name,
            ws.name,
            wf.fueltech_id as fueltech,
            f.label as fueltech_label,
            wf.status_id as status,
            fs.label as status_label,
            ws.code as station_code,
            ws.boundary as station_boundary,
            ST_AsGeoJSON(ws.geom) as station_point,
            ws.state,
            ws.postcode,
            ST_X(ws.geom),
            ST_Y(ws.geom),
            ST_AsText(ws.geom),
            ws.name_clean,
            ws.id,
            wf.region,
            wf.unit_number,
            wf.unit_size,
            ws.id
        from nem_station ws
        join nem_facility wf on wf.station_id = ws.id
        join fueltech f on f.code = wf.fueltech_id
        join facility_status fs on fs.code = wf.status_id
        order by ws.id asc
    """
    query = __sql.format()
    features = []
    current_name = None
    current_station_code = None
    f = None

    with engine.connect() as c:

        rows = c.execute(query)

        for row in rows:
            if current_station_code != row[18]:

                if f is not None:
                    features.append(f)

                f = Feature()
                current_station_code = row[18]

                if row[11]:
                    f.geometry = Point((row[15], row[14]))

                f.properties = {
                    "oid": "nem_{}".format(row[22]),
                    "station_id": row[18],
                    "station_code": row[9] or row[0],
                    "facility_id": row[0],
                    "network": "NEM",
                    "network_region": row[19],
                    "state": row[12] or row[19][:-1],
                    "postcode": row[13],
                    "name": row[17] or row[4],
                    "registered_capacity": float(row[1]) if row[1] else None,
                    "duid_data": [],
                }

            f.properties["duid_data"].append(
                {
                    "duid": row[0],
                    "fuel_tech": row[5],
                    "commissioned_date": row[2].isoformat()
                    if type(row[2]) is datetime
                    else str(row[2]),
                    "fuel_tech_label": row[6],
                    "status": row[7],
                    "status_label": row[8],
                    "unit_number": row[20],
                    "unit_size": str(row[21]),
                    "registered_capacity": float(row[1]) if row[1] else None,
                }
            )

    if f:
        features.append(f)

    return features


if __name__ == "__main__":
    wf = wem_export()
    nf = nem_export()

    crs = {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
    }

    geoj = FeatureCollection(nf + wf, crs=crs, name="opennem")

    geoj["name"] = "nem_facilities"
    geoj["crs"] = crs

    with open("data/facility_diff/au_facilities.json", "w",) as fh:
        fh.write(dumps(geoj, indent=4))

    with open(
        "s3://data.opennem.org.au/v3/geo/au_facilities.json",
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        fh.write(dumps(geoj, indent=4))
