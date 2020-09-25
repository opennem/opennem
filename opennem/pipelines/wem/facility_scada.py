import csv
import logging
from datetime import datetime, timedelta

import pytz
from sqlalchemy.sql import text

from opennem.db.models.opennem import FacilityScada
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


wem_timezone = pytz.timezone("Australia/Perth")


class WemStoreFacilityScada(DatabaseStoreBase):
    def parse_interval(self, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        dt_aware = wem_timezone.localize(dt)

        return dt_aware

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        csvreader = csv.DictReader(item["content"].split("\n"))

        # Get all facility codes
        #  It's faster to do this and bulk insert than it is to
        #  catch integrityerrors

        q = self.engine.execute(text("select code from facility"))

        all_facilities = list(set([i[0] for i in q.fetchall()]))

        objects = []
        keys = []

        for row in csvreader:
            if row["Facility Code"] not in all_facilities:
                continue

            row_key = "{}_{}".format(
                row["Trading Interval"], row["Facility Code"]
            )

            item = FacilityScada(
                network_id="WEM",
                trading_interval=self.parse_interval(row["Trading Interval"]),
                facility_code=row["Facility Code"],
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


class WemStoreLiveFacilityScada(DatabaseStoreBase):
    """
        Store live facility scada data.

    """

    def parse_interval(self, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        dt_aware = wem_timezone.localize(dt)

        return dt_aware

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        csvreader = csv.DictReader(item["content"].split("\n"))

        # Get all facility codes

        q = self.engine.execute(text("select distinct code from facility"))

        all_facilities = list(set([i[0] for i in q.fetchall()]))

        objects = []
        keys = []
        last_asat = None

        for row in csvreader:
            if not row["FACILITY_CODE"] in all_facilities:
                logger.error(
                    "Do not have facility: {}".format(row["FACILITY_CODE"])
                )
                continue

            if row["AS_AT"] != "":
                last_asat = self.parse_interval(row["AS_AT"])

            if not last_asat or type(last_asat) is not datetime:
                logger.error("Invalid row or no datetime")
                continue

            # We need to pivot the table since columns are time intervals
            for i in range(1, 48):

                column = f"I{i:02}"

                if column not in row:
                    logger.error(
                        "Do not have data for interval {}".format(column)
                    )
                    continue

                if i > 0:
                    interval = last_asat - timedelta(minutes=(i - 1) * 30)
                else:
                    interval = last_asat

                row_key = "{}_{}".format(interval, row["FACILITY_CODE"])

                val = None

                try:
                    val = float(row[column]) / 2 or None
                except ValueError:
                    pass

                item = FacilityScada(
                    trading_interval=interval,
                    facility_code=row["FACILITY_CODE"],
                    generated=val,
                )

                if row_key not in keys:
                    # objects.append(item)
                    s.add(item)
                    # s.save()
                    keys.append(row_key)

        try:
            # s.bulk_save_objects(objects)
            s.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return len(objects)
