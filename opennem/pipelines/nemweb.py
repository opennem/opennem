import logging

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.nemweb import DISPATCHUNITSCADA
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

TABLE_MAP = {"DISPATCH_UNIT_SCADA": DISPATCHUNITSCADA}


class NemwebMirror(object):
    def __init__(self):
        engine = db_connect()
        self.session = sessionmaker(bind=engine)

    @check_spider_pipeline
    def process_item(self, item, spider):
        oitem = item.copy()

        s = self.session()

        if not "name" in item:
            return item

        table_name = item["name"]

        if not table_name in TABLE_MAP:
            logger.error(
                "Could not map table name to model for item {}".format(table_name)
            )
            return item

        Model = TABLE_MAP[table_name]

        if not "records" in item:
            logger.info("No records for item with table name {}".format(table_name))
            return item

        records = item["records"]

        for record in records:

            i = Model(**record)

            try:
                s.add(i)
                s.commit()
            except Exception as e:
                s.rollback()
                logger.error("Database error: {}".format(e))
                logger.debug(i.__dict__)
            finally:
                s.close()

        return item
