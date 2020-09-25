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


class WemStoreBalancingSummary(DatabaseStoreBase):
    def parse_interval(self, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        dt_aware = wem_timezone.localize(dt)

        return dt_aware

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        csvreader = csv.DictReader(item["content"].split("\n"))

        q = self.engine.execute(
            text(
                "select max(trading_interval) from balancing_summary where network_id='WEM'"
            )
        )

        interval_max = q.fetchone()[0] or wem_timezone.localize(
            datetime(1900, 1, 1, 0, 0, 0)
        )

        objects = [
            BalancingSummary(
                network_id="WEM",
                trading_interval=self.parse_interval(row["Trading Interval"]),
                forecast_load=row["Load Forecast (MW)"],
                generation_scheduled=row["Scheduled Generation (MW)"],
                generation_non_scheduled=row["Non-Scheduled Generation (MW)"],
                generation_total=row["Total Generation (MW)"],
                price=row["Final Price ($/MWh)"],
            )
            for row in csvreader
            if self.parse_interval(row["Trading Interval"]) > interval_max
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


class WemStoreBalancingSummaryArchive(DatabaseStoreBase):
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
                network_id="WEM",
                trading_interval=self.parse_interval(row["Trading Interval"]),
                forecast_load=row["Load Forecast (MW)"],
                generation_scheduled=row["Scheduled Generation (MW)"],
                generation_non_scheduled=row["Non-Scheduled Generation (MW)"],
                generation_total=row["Total Generation (MW)"],
                price=row["Final Price ($/MWh)"],
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
