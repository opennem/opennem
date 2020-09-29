"""

NEMWEB Data ingress into OpenNEM format


"""

import logging
from datetime import datetime

import pytz
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import text

from opennem.core.normalizers import normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.schema.opennem import NetworkNEM
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

nemweb_timezone = pytz.timezone(NetworkNEM.timezone)


def parse_nemweb_interval(interval: str) -> datetime:

    if type(interval) is datetime:
        dt = interval
        return interval

    dt = datetime.strptime(interval, "%Y/%m/%d %H:%M:%S")

    dt_aware = nemweb_timezone.localize(dt)

    return dt_aware


def process_case_solutions(table):
    session = SessionLocal()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    records_to = []


def process_unit_scada(table):
    session = SessionLocal()
    engine = get_database_engine()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    records_to_store = []

    for record in records:
        records_to_store.append(
            {
                "trading_interval": parse_nemweb_interval(
                    record["SETTLEMENTDATE"]
                ),
                "facility_code": normalize_duid(record["DUID"]),
                "generated": float(record["SCADAVALUE"]),
                "network_id": "NEM",
            }
        )

    logger.debug("Saving %d records", len(records_to_store))

    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        constraint="facility_scada_pkey",
        set_={
            "eoi_quantity": stmt.excluded.eoi_quantity,
            "generated": stmt.excluded.generated,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error: {}".format(e))
    finally:
        session.close()


TABLE_PROCESSOR_MAP = {
    "DISPATCH_CASE_SOLUTION": "process_case_solutions",
    "DISPATCH_UNIT_SCADA": "process_unit_scada",
}


class NemwebUnitScadaOpenNEMStorePipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        if "tables" not in item and type(item["tables"]) is not list:
            raise Exception("Invalid item - no tables located")

        tables = item["tables"]

        for table in tables:
            if "name" not in table:
                logger.info("Invalid table found")
                continue

            table_name = table["name"]

            if table_name not in TABLE_PROCESSOR_MAP:
                logger.info("No processor for table %s", table_name)
                continue

            process_meth = TABLE_PROCESSOR_MAP[table_name]

            if process_meth not in globals():
                logger.info("Invalid processing function %s", process_meth)
                continue

            globals()[process_meth](table)
