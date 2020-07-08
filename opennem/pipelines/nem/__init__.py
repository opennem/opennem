import csv
import logging

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import NemDispatchPrice, NemDispatchUnitScada
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

TABLE_MAP = {
    "DISPATCH_UNIT_SCADA": NemDispatchUnitScada,
    "DISPATCH_PRICE": NemDispatchPrice,
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

            if record_type == "C":
                # @TODO csv meta stored in table
                if table["name"] is not None:
                    item["tables"].append(table)

            elif record_type == "I":
                if table["name"] is not None:
                    item["tables"].append(table)

                table = {}
                table["name"] = "{}_{}".format(row[1], row[2])
                table["fields"] = fields = row[4:]
                table["records"] = []

            elif record_type == "D":
                values = row[4:]
                record = dict(zip(table["fields"], values))

                table["records"].append(record)

        return item


class DatabaseStore(object):
    def __init__(self):
        engine = db_connect()
        self.session = sessionmaker(bind=engine)

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
