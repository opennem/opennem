"""

NEMWEB Data ingress into OpenNEM format


"""

import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.core.normalizers import normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.schema.opennem import NetworkNEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def process_case_solutions(table):
    pass
    # session = SessionLocal()

    # if "records" not in table:
    #     raise Exception("Invalid table no records")

    # records = table["records"]

    # records_to = []


def process_meter_data_gen_duid(table, spider):
    session = SessionLocal()
    engine = get_database_engine()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    records_to_store = []

    for record in records:
        trading_interval = parse_date(
            record["INTERVAL_DATETIME"], network=NetworkNEM, dayfirst=False
        )

        if not trading_interval:
            continue

        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": spider.name,
                # "updated_by": None,
                "trading_interval": trading_interval,
                "facility_code": normalize_duid(record["DUID"]),
                "eoi_quantity": record["MWH_READING"],
            }
        )

    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        constraint="facility_scada_pkey",
        set_={"eoi_quantity": stmt.excluded.eoi_quantity},
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error inserting records")
        logger.error(e)
        return 0
    finally:
        session.close()

    return len(records_to_store)


def process_pre_ap_price(table, spider):
    session = SessionLocal()
    engine = get_database_engine()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    records_to_store = []

    for record in records:
        trading_interval = parse_date(
            record["SETTLEMENTDATE"], network=NetworkNEM, dayfirst=False
        )

        if not trading_interval:
            continue

        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": spider.name,
                # "updated_by": None,
                "network_region": record["REGIONID"],
                "trading_interval": trading_interval,
                "price": record["PRE_AP_ENERGY_PRICE"],
            }
        )

    stmt = insert(BalancingSummary).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        constraint="balancing_summary_pkey",
        set_={"price": stmt.excluded.price},
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error inserting records")
        logger.error(e)
        return 0
    finally:
        session.close()

    return len(records_to_store)


def process_unit_scada(table, spider):
    session = SessionLocal()
    engine = get_database_engine()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    records_to_store = []
    records_primary_keys = []

    for record in records:
        trading_interval = parse_date(
            record["SETTLEMENTDATE"], network=NetworkNEM, dayfirst=False
        )
        facility_code = normalize_duid(record["DUID"])

        if not trading_interval or not facility_code:
            continue

        # Since this can insert 1M+ records at a time we need to
        # do a separate in-memory check of primary key constraints
        # better way of doing this .. @TODO
        _unique_set = (trading_interval, facility_code, "NEM")

        if _unique_set not in records_primary_keys:

            records_to_store.append(
                {
                    "network_id": "NEM",
                    "created_by": spider.name,
                    # "updated_by": None,
                    "trading_interval": trading_interval,
                    "facility_code": facility_code,
                    "generated": float(record["SCADAVALUE"]),
                }
            )

            records_primary_keys.append(_unique_set)

    # free
    records_primary_keys = []

    logger.debug("Saving %d records", len(records_to_store))

    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        constraint="facility_scada_pkey",
        set_={"generated": stmt.excluded.generated},
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error: {}".format(e))
        return 0
    finally:
        session.close()

    return len(records_to_store)


def process_unit_solution(table, spider):
    session = SessionLocal()
    engine = get_database_engine()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    records_to_store = []
    records_primary_keys = []

    for record in records:
        trading_interval = parse_date(
            record["SETTLEMENTDATE"], network=NetworkNEM, dayfirst=False
        )
        facility_code = normalize_duid(record["DUID"])

        if not trading_interval or not facility_code:
            continue

        # Since this can insert 1M+ records at a time we need to
        # do a separate in-memory check of primary key constraints
        # better way of doing this .. @TODO
        _unique_set = (trading_interval, facility_code, "NEM")

        if _unique_set not in records_primary_keys:

            records_to_store.append(
                {
                    "network_id": "NEM",
                    "created_by": spider.name,
                    # "updated_by": None,
                    "trading_interval": trading_interval,
                    "facility_code": facility_code,
                    "eoi_quantity": float(record["INITIALMW"]),
                }
            )
            records_primary_keys.append(_unique_set)

    # free
    records_primary_keys = []

    logger.debug("Saving %d records", len(records_to_store))

    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        constraint="facility_scada_pkey",
        set_={"eoi_quantity": stmt.excluded.eoi_quantity},
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error: {}".format(e))
        return 0
    finally:
        session.close()

    return len(records_to_store)


TABLE_PROCESSOR_MAP = {
    "METER_DATA_GEN_DUID": "process_meter_data_gen_duid",
    "DISPATCH_CASE_SOLUTION": "process_case_solutions",
    "DISPATCH_UNIT_SCADA": "process_unit_scada",
    "DISPATCH_UNIT_SOLUTION": "process_unit_solution",
    "DISPATCH_PRE_AP_PRICE": "process_pre_ap_price",
}


class NemwebUnitScadaOpenNEMStorePipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        if "tables" not in item:
            logger.error("Invalid item - no tables located")
            return 0

        if not isinstance(item["tables"], list):
            logger.error("Invalid item - no tables located")
            return 0

        tables = item["tables"]

        ret = 0

        for table in tables:
            if "name" not in table:
                logger.info("Invalid table found")
                continue

            table_name = table["name"]

            if table_name not in TABLE_PROCESSOR_MAP:
                logger.error("No processor for table %s", table_name)
                continue

            process_meth = TABLE_PROCESSOR_MAP[table_name]

            if process_meth not in globals():
                logger.info("Invalid processing function %s", process_meth)
                continue

            ret += globals()[process_meth](table, spider=spider)

        return ret
