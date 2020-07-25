import csv
import logging
import zipfile

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.opennem import DispatchPrice, DispatchUnitScada
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

TABLE_MAP = {
    "DISPATCH_UNIT_SCADA": DispatchUnitScada,
    "DISPATCH_PRICE": DispatchPrice,
}


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
