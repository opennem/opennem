import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from opennem.db.models.opennem import BalancingSummary
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

from .facility_scada import wem_timezone

logger = logging.getLogger(__name__)


class WemStorePulse(DatabaseStoreBase):
    def parse_interval(self, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        dt_aware = wem_timezone.localize(dt)

        return dt_aware

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        csvreader = csv.DictReader(item["content"].split("\n"))

        objects = [
            BalancingSummary(
                trading_interval=self.parse_interval(
                    row["TRADING_DAY_INTERVAL"]
                ),
                forecast_load=row["FORECAST_EOI_MW"],
                # generation_scheduled=row["Scheduled Generation (MW)"],
                # generation_non_scheduled=row["Non-Scheduled Generation (MW)"],
                # generation_total=row["Total Generation (MW)"],
                price=row["PRICE"],
            )
            for row in csvreader
        ]

        try:
            s.bulk_save_objects(objects)
            s.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
            raise e
        finally:
            s.close()

        return len(objects)
