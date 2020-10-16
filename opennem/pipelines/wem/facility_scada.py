import csv
import logging
from datetime import datetime, timedelta
from io import StringIO

from sqlalchemy.dialects.postgresql import insert

from opennem.core.normalizers import clean_float, normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.pipelines import DatabaseStoreBase
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def generate_records(csvreader, spider=None):
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


sql = """
CREATE TEMP TABLE __tmp
(LIKE facility_scada INCLUDING DEFAULTS)
ON COMMIT DROP;

COPY __tmp FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ',');

INSERT INTO facility_scada
    SELECT *
    FROM __tmp
ON CONFLICT (trading_interval, network_id, facility_code) DO UPDATE set
    generated = EXCLUDED.generated,
    eoi_quantity = EXCLUDED.eoi_quantity
;
"""


class WemStoreFacilityScada(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        csvreader = csv.DictReader(item["content"].split("\n"))

        csv_buffer = StringIO()

        fieldnames = [
            "created_by",
            "created_at",
            "updated_at",
            "network_id",
            "trading_interval",
            "facility_code",
            "generated",
            "eoi_quantity",
        ]

        csvwriter = csv.DictWriter(csv_buffer, fieldnames=fieldnames,)

        for record in generate_records(csvreader, spider):
            csvwriter.writerow(record)

        conn = get_database_engine().raw_connection()

        cursor = conn.cursor()
        csv_buffer.seek(0)

        cursor.copy_expert(sql, csv_buffer)

        conn.commit()


class WemStoreLiveFacilityScada(DatabaseStoreBase):
    """
        Store live facility scada data.

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


class WemStoreFacilityIntervals(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        session = SessionLocal()
        engine = get_database_engine()

        csvreader = csv.DictReader(item["content"].split("\n"))

        records_to_store = []

        for row in csvreader:
            trading_interval = parse_date(
                row["PERIOD"], network=NetworkWEM, dayfirst=False
            )
            facility_code = normalize_duid(row["FACILITY_CODE"])

            energy = 0.0

            if "POTENTIAL_MWH" in row:
                energy = clean_float(row["POTENTIAL_MWH"])

                # @NOTE - don't use
                energy = 0.0

            records_to_store.append(
                {
                    "created_by": spider.name,
                    "network_id": "WEM",
                    "trading_interval": trading_interval,
                    "facility_code": facility_code,
                    "generated": row["ACTUAL_MW"] or None,
                    "eoi_quantity": energy,
                }
            )

        stmt = insert(FacilityScada).values(records_to_store)
        stmt.bind = engine
        stmt = stmt.on_conflict_do_update(
            index_elements=["trading_interval", "network_id", "facility_code"],
            set_={
                # "updated_by": stmt.excluded.created_by,
                "generated": stmt.excluded.generated,
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
