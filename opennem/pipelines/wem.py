import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.wem import WemFacility, WemFacilityScada, WemParticipant
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

TABLE_MAP = {
    "facilities": WemFacility,
    "facility_scada": WemFacilityScada,
}


class ExtractCSV(object):
    @check_spider_pipeline
    def process_item(self, item, spider):

        if not "content" in item:
            return item

        content = item["content"]
        del item["content"]

        item["tables"] = []
        table = {"name": None}

        datacsv = csv.reader(content.split("\n"))

        for row in datacsv:
            if not row or type(row) is not list or len(row) < 1:
                continue

            record_type = row[0]
            record = row
            table["records"].append(record)

        return item


FACILITY_MAP = {
    "Balancing Status": "active",
}


class DatabaseStore(object):
    def __init__(self):
        engine = db_connect()
        self.session = sessionmaker(bind=engine)

    def facility(self, row):
        pass

        s = self.session()
        from pprint import pprint

        if not "Participant Code" in row:
            print("invlid row")
            return row

        participant = None

        participant_code = row["Participant Code"]
        participant = s.query(WemParticipant).get(participant_code)

        if not participant:
            print("Participant not found: {}".format(participant_code))
            participant = WemParticipant(
                code=participant_code, name=row["Participant Name"]
            )
            s.add(participant)
            s.commit()

        facility = None

        facility_code = row["Facility Code"]
        facility = s.query(WemFacility).get(facility_code)

        if not facility:
            facility = WemFacility(
                code=facility_code, participant=participant,
            )

        facility.active = (
            False if row["Balancing Status"] == "Non-Active" else True
        )

        if row["Capacity Credits (MW)"]:
            facility.capacity_credits = row["Capacity Credits (MW)"]

        if row["Maximum Capacity (MW)"]:
            facility.capacity_maximum = row["Maximum Capacity (MW)"]

        registered_date = row["Registered From"]

        if registered_date:
            registered_date_dt = datetime.strptime(
                registered_date, "%Y-%m-%d %H:%M:%S"
            )
            facility.registered = registered_date_dt

        s.add(facility)
        s.commit()

    @check_spider_pipeline
    def process_item(self, item, spider):

        s = self.session()

        if not "tables" in item:
            logger.info("No tables in item to process")
            return item

        tables = item["tables"]

        for table in tables:

            if not "name" in table:
                logger.error("No name in table")
                continue

            table_name = table["name"]

            if not table_name in TABLE_MAP:
                logger.error(
                    "Could not map table name to model for item {}".format(
                        table_name
                    )
                )
                continue

            Model = TABLE_MAP[table_name]

            if not "records" in table:
                logger.info(
                    "No records for item with table name {}".format(table_name)
                )
                continue

            records = table["records"]

            for record in records:

                i = Model(**record)

                try:
                    s.add(i)
                    s.commit()
                except IntegrityError:
                    pass
                except Exception as e:
                    s.rollback()
                    logger.error("Database error: {}".format(e))
                    logger.debug(i.__dict__)
                finally:
                    s.close()

        s.close()

        return item
