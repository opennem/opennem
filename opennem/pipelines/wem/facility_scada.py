import csv
import logging
from datetime import datetime, timedelta
from io import StringIO

from sqlalchemy.dialects.postgresql import insert

from opennem.core.normalizers import clean_float, normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def facility_scada_generate_records(csvreader, spider=None):
    created_at = datetime.now()
    primary_keys = []

    for row in csvreader:
        trading_interval = parse_date(
            row["Trading Interval"], network=NetworkWEM, dayfirst=False
        )
        facility_code = normalize_duid(row["Facility Code"])

        pkey = (trading_interval, facility_code)

        if pkey in primary_keys:
            continue

        primary_keys.append(pkey)

        generated = 0.0
        generated_field = "EOI Quantity (MW)"

        if generated_field in row:
            generated = clean_float(row[generated_field])

        energy = 0.0
        energy_field = "Energy Generated (MWh)"

        if energy_field in row:
            energy = clean_float(row[energy_field])

        created_by = ""

        if spider and hasattr(spider, "name"):
            created_by = spider.name

        yield {
            "created_by": created_by,
            "created_at": created_at,
            "updated_at": None,
            "network_id": "WEM",
            "trading_interval": trading_interval,
            "facility_code": facility_code,
            "generated": generated,
            "eoi_quantity": energy,
        }


class WemStoreFacilityScada(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if "content" not in item:
            logger.error("No item content slipping store facility scada")
            return item

        csvreader = csv.DictReader(item["content"].split("\n"))

        item["table_schema"] = FacilityScada
        item["update_fields"] = ["generated", "eoi_quantity"]
        item["records"] = list(
            facility_scada_generate_records(csvreader, spider)
        )
        item["content"] = None

        return item


def facility_intervals_generate_records(csvreader, spider=None):
    created_at = datetime.now()
    primary_keys = []

    for row in csvreader:

        interval_field = "PERIOD"

        trading_interval = parse_date(
            row[interval_field], network=NetworkWEM, dayfirst=False
        )

        facility_code_field = "FACILITY_CODE"

        if facility_code_field not in row:
            logger.error("Invalid row no facility_code")
            continue

        facility_code = normalize_duid(row[facility_code_field])

        pkey = (trading_interval, facility_code)

        if pkey in primary_keys:
            continue

        primary_keys.append(pkey)

        generated = 0.0
        generated_field = "ACTUAL_MW"

        if generated_field in row:
            generated = clean_float(row[generated_field])

        energy = 0.0
        energy_field = "POTENTIAL_MWH"

        if energy_field in row:
            # figure out what to do with this
            # energy = clean_float(row[energy_field])
            pass

        created_by = ""

        if spider and hasattr(spider, "name"):
            created_by = spider.name

        yield {
            "created_by": created_by,
            "created_at": created_at,
            "updated_at": None,
            "network_id": "WEM",
            "trading_interval": trading_interval,
            "facility_code": facility_code,
            "generated": generated,
            "eoi_quantity": energy,
        }


class WemStoreFacilityIntervals(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if "content" not in item:
            logger.error("No item content slipping store facility scada")
            return item

        csvreader = csv.DictReader(item["content"].split("\n"))

        item["table_schema"] = FacilityScada
        item["update_fields"] = ["generated", "eoi_quantity"]
        item["records"] = list(
            facility_intervals_generate_records(csvreader, spider)
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

