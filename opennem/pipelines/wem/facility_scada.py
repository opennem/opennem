import csv
import logging
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import insert

from opennem.core.normalizers import normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.pipelines.nem.opennem import unit_scada_generate_facility_scada
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStoreFacilityScada(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if "content" not in item:
            logger.error("No item content slipping store facility scada")
            return item

        csvreader = csv.DictReader(item["content"].split("\n"))

        item["table_schema"] = FacilityScada
        item["update_fields"] = ["generated", "eoi_quantity"]
        item["records"] = unit_scada_generate_facility_scada(
            csvreader,
            spider,
            interval_field="Trading Interval",
            facility_code_field="Facility Code",
            power_field="EOI Quantity (MW)",
            energy_field="Energy Generated (MWh)",
            network=NetworkWEM,
        )
        item["content"] = None

        return item


class WemStoreFacilityIntervals(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if "content" not in item:
            logger.error("No item content slipping store facility scada")
            return item

        csvreader = csv.DictReader(item["content"].split("\n"))

        item["table_schema"] = FacilityScada
        item["update_fields"] = ["generated", "eoi_quantity"]
        item["records"] = unit_scada_generate_facility_scada(
            csvreader,
            spider,
            interval_field="PERIOD",
            facility_code_field="FACILITY_CODE",
            power_field="ACTUAL_MW",
            network=NetworkWEM,
        )
        item["content"] = None

        return item


class WemStoreLiveFacilityScada(object):
    """
        Store live facility scada data.

        @NOTE no longer used

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        session = SessionLocal()
        engine = get_database_engine()

        csvreader = csv.DictReader(item["content"].split("\n"))

        records_to_store = []
        last_asat = None

        for row in csvreader:

            # @TODO MAX_GEN_CAPACITY
            # facility_capacity = row["MAX_GEN_CAPACITY"]

            if row["AS_AT"] != "":
                last_asat = parse_date(
                    row["AS_AT"], network=NetworkWEM, dayfirst=False
                )

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

                val = None

                try:
                    val = float(row[column]) / 2 or None
                except ValueError:
                    pass

                records_to_store.append(
                    {
                        "created_by": spider.name,
                        "network_id": "WEM",
                        "trading_interval": interval,
                        "facility_code": facility_code,
                        "eoi_quantity": val,
                    }
                )

        stmt = insert(FacilityScada).values(records_to_store)
        stmt.bind = engine
        stmt = stmt.on_conflict_do_update(
            index_elements=["trading_interval", "network_id", "facility_code"],
            set_={
                # "updated_by": stmt.excluded.created_by,
                "eoi_quantity": stmt.excluded.eoi_quantity,
            },
        )

        try:
            session.execute(stmt)
            session.commit()
        except Exception as e:
            logger.error("Error inserting records")
            logger.error(e)
        finally:
            session.close()

        return len(records_to_store)

