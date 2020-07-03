import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from opennem.db.models.wem import WemFacilityScada
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStoreFacilityScada(DatabaseStoreBase):
    def parse_interval(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        csvreader = csv.DictReader(item["content"].split("\n"))

        # Get all facility codes
        #  It's faster to do this and bulk insert than it is to
        #  catch integrityerrors

        q = self.engine.execute(text("select code from wem_facility"))

        all_facilities = list(set([i[0] for i in q.fetchall()]))

        objects = []
        keys = []

        for row in csvreader:
            if not row["Facility Code"] in all_facilities:
                continue

            row_key = "{}_{}".format(
                row["Trading Interval"], row["Facility Code"]
            )

            item = WemFacilityScada(
                trading_interval=self.parse_interval(row["Trading Interval"]),
                facility_id=row["Facility Code"],
                eoi_quantity=row["EOI Quantity (MW)"] or None,
                generated=row["Energy Generated (MWh)"] or None,
            )

            if row_key not in keys:
                objects.append(item)
                keys.append(row_key)

        try:
            s.bulk_save_objects(objects)
            s.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return len(objects)
