import logging
from datetime import datetime
from pprint import pprint

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from opennem.db import db_connect
from opennem.db.models.opennem import NemFacility
from opennem.geo.google_geo import place_search

logger = logging.getLogger(__name__)


def nem_geocode():
    engine = db_connect()
    session = sessionmaker(bind=engine)
    s = session()

    records = s.query(NemFacility).filter(NemFacility.geom == None)

    limit = 50
    count = 0
    skipped = 0
    records_added = 0

    for r in records:
        geo_str = "{}, {}, Australia".format(r.name, r.region[:-1])

        logger.info("Encoding: {}".format(geo_str))

        google_result = place_search(geo_str)

        pprint(google_result)

        if (
            google_result
            and type(google_result) is list
            and len(google_result) > 0
        ):
            result = google_result[0]

            r.place_id = result["place_id"]

            lat = result["geometry"]["location"]["lat"]
            lng = result["geometry"]["location"]["lng"]
            r.geom = "SRID=4326;POINT({} {})".format(lat, lng)

            try:
                s.add(r)
                s.commit()
                records_added += 1
            except IntegrityError as e:
                logger.error(e)
                skipped += 1
                pass
            except Exception as e:
                skipped += 1
                logger.error("Error: {}".format(e))
        else:
            skipped += 1

        count += 1
        if count >= limit:
            break

    print(
        "Done. Added {} records. Couldn't match {}".format(
            records_added, skipped
        )
    )


if __name__ == "__main__":
    nem_geocode()
