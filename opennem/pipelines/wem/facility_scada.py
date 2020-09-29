import csv
import logging
from datetime import datetime, timedelta

import pytz
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import text

from opennem.core.normalizers import normalize_duid
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

        objects = []

        for row in csvreader:
            trading_interval = self.parse_interval(row["Trading Interval"])
            facility_code = normalize_duid(row["Facility Code"])

            objects.append(
                {
                    "network_id": "WEM",
                    "trading_interval": trading_interval,
                    "facility_code": facility_code,
                    "eoi_quantity": row["EOI Quantity (MW)"] or None,
                    "generated": row["Energy Generated (MWh)"] or None,
                }
            )

        stmt = insert(FacilityScada).values(objects)
        stmt.bind = self.engine
        stmt = stmt.on_conflict_do_update(
            constraint="facility_scada_pkey",
            set_={
                "eoi_quantity": stmt.excluded.eoi_quantity,
                "generated": stmt.excluded.generated,
            },
        )

        try:
            r = s.execute(stmt)
            s.commit()
            return r
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return None


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

        q = self.engine.execute(
            text(
                """ select trading_interval, facility_code
                    from facility_scada where network_id='WEM'
                """
            )
        )

        keys = [(i[0], normalize_duid(i[1])) for i in q.fetchall()]

        objects = []
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

                facility_code = normalize_duid(row["FACILITY_CODE"])

                row_key = (interval, facility_code)

                val = None

                try:
                    val = float(row[column]) / 2 or None
                except ValueError:
                    pass

                item = FacilityScada(
                    network_id="WEM",
                    trading_interval=interval,
                    facility_code=facility_code,
                    generated=val,
                )

                if row_key not in keys:
                    # objects.append(item)
                    # s.save()
                    s.add(item)
                    keys.append(row_key)

        try:
            # s.bulk_save_objects(objects)
            s.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return len(objects)
