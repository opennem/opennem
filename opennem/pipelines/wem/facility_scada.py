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

        # Get all intervals

        q = self.engine.execute(
            text("select distinct trading_interval from wem_balancing_summary")
        )

        all_intervals = list(set([i[0] for i in q.fetchall()]))

        # Get all facility codes

        q = self.engine.execute(text("select code from wem_facility"))

        all_facilities = list(set([i[0] for i in q.fetchall()]))

        objects = [
            WemFacilityScada(
                trading_interval=self.parse_interval(row["Trading Interval"]),
                facility_id=row["Facility Code"],
                eoi_quantity=row["EOI Quantity (MW)"] or 0,
                generated=row["Energy Generated (MWh)"] or 0,
            )
            for row in csvreader
            if self.parse_interval(row["Trading Interval"])
            not in all_intervals
            and row["Energy Generated (MWh)"] != ""
            and row["Facility Code"] in all_facilities
        ]

        try:
            s.bulk_save_objects(objects)
            s.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return len(objects)
