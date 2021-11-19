"""OpenNEM Core Controller

Parses MMS tables into OpenNEM derived database
"""

import logging
from datetime import datetime
from itertools import groupby
from typing import Any, Dict, List, Optional

from scrapy import Spider
from sqlalchemy.dialects.postgresql import insert

from opennem.core.networks import NetworkNEM
from opennem.core.normalizers import clean_float, normalize_duid
from opennem.core.parsers.aemo.mms import AEMOTableSchema, AEMOTableSet
from opennem.db import SessionLocal, get_database_engine
from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary, Facility, FacilityScada
from opennem.importer.rooftop import rooftop_remap_regionids
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkAEMORooftop, NetworkSchema, NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.numbers import float_to_str
from opennem.utils.sql import duid_in_case

logger = logging.getLogger("opennem.controllers.opennem")

# Return Schema


class ControllerReturn(BaseConfig):
    total_records: int = 0
    inserted_records: int = 0
    processed_records: int = 0
    errors: int = 0
    error_detail: Optional[str]


# Helpers


def unit_scada_generate_facility_scada(
    records,
    network: NetworkSchema = NetworkNEM,
    interval_field: str = "settlementdate",
    facility_code_field: str = "duid",
    power_field: Optional[str] = "scadavalue",
    energy_field: Optional[str] = None,
    is_forecast: bool = False,
) -> List[Dict]:
    created_at = datetime.now()
    return_records = []

    created_by = "opennem.controller"

    for row in records:
        __rec = {
            "created_by": "opennem.controller",
            "created_at": created_at,
            "updated_at": None,
            "network_id": network.code,
            "trading_interval": getattr(row, interval_field),
            "facility_code": getattr(row, facility_code_field),
            "generated": getattr(row, power_field),
            "eoi_quantity": None,
            "is_forecast": is_forecast,
            "energy_quality_flag": 0,
        }

        return_records.append(__rec)

    return return_records


def generate_balancing_summary(
    records: List[Dict],
    spider: Spider,
    interval_field: str = "SETTLEMENTDATE",
    network_region_field: str = "REGIONID",
    price_field: Optional[str] = None,
    network: NetworkSchema = NetworkNEM,
    limit: int = 0,
) -> List[Dict]:
    created_at = datetime.now()
    # primary_keys = []
    return_records = []

    created_by = ""

    if spider and hasattr(spider, "name"):
        created_by = spider.name

    for row in records:

        trading_interval = parse_date(row[interval_field], network=network, dayfirst=False)

        network_region = None

        if network_region_field and network_region_field in row:
            network_region = row[network_region_field]

        price = None

        if price_field and price_field in row:
            price = clean_float(row[price_field])

            if price:
                price = float_to_str(price)

        __rec = {
            "created_by": created_by,
            "created_at": created_at,
            "updated_at": None,
            "network_id": network.code,
            "network_region": network_region,
            "trading_interval": trading_interval,
            "price": price,
        }

        return_records.append(__rec)

        if limit > 0 and len(return_records) >= limit:
            break

    return return_records


# Processors


def process_dispatch_interconnectorres(table: AEMOTableSchema) -> ControllerReturn:
    session = SessionLocal()
    engine = get_database_engine()

    cr = ControllerReturn(total_records=len(table.records))
    records_to_store = []

    for record in table.records:
        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": "opennem.controller",
                "facility_code": record.interconnectorid,
                "trading_interval": record.settlementdate,
                "generated": record.mwflow,
            }
        )
        cr.processed_records += 1

    # insert
    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "facility_code", "is_forecast"],
        set_={"generated": stmt.excluded.generated},
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error inserting records")
        logger.error(e)
        cr.errors = cr.processed_records
        return cr
    finally:
        session.close()

    cr.inserted_records = cr.processed_records
    return cr


def process_nem_price(table: AEMOTableSchema) -> ControllerReturn:
    session = SessionLocal()
    engine = get_database_engine()

    cr = ControllerReturn(total_records=len(table.records))
    records_to_store = []

    price_field = "price"

    if table.full_name == "dispatch_price":
        price_field = "price_dispatch"

    for record in table.records:
        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": "opennem.controllers.nem",
                "network_region": record.regionid,
                "trading_interval": record.settlementdate,
                price_field: record.rrp,
            }
        )

        cr.processed_records += 1

    stmt = insert(BalancingSummary).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "network_region"],
        set_={price_field: getattr(stmt.excluded, price_field)},
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error inserting NEM price records")
        logger.error(e)
        cr.errors = cr.processed_records
        return cr
    finally:
        session.close()

    cr.inserted_records = cr.processed_records
    return cr


def process_dispatch_regionsum(table: AEMOTableSchema) -> ControllerReturn:
    session = SessionLocal()
    engine = get_database_engine()

    cr = ControllerReturn(total_records=len(table.records))
    records_to_store = []

    for record in table.records:
        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": "opennem.controller",
                "network_region": record.regionid,
                "trading_interval": record.settlementdate,
                "net_interchange": record.netinterchange,
                "demand_total": record.demand_and_nonschedgen,
            }
        )

        cr.processed_records += 1

    stmt = insert(BalancingSummary).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "network_region"],
        set_={
            "net_interchange": stmt.excluded.net_interchange,
            "demand_total": stmt.excluded.demand_total,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error inserting records")
        logger.error(e)
        cr.errors = cr.processed_records
        return cr

    finally:
        session.close()

    cr.inserted_records = cr.processed_records
    return cr


def process_trading_regionsum(table: Dict[str, Any], spider: Spider) -> Dict:
    session = SessionLocal()
    engine = get_database_engine()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    limit = None
    records_to_store = []
    records_processed = 0
    primary_keys = []

    for record in records:
        trading_interval = parse_date(
            record["SETTLEMENTDATE"],
            network=NetworkNEM,
            dayfirst=False,
            date_format="%Y/%m/%d %H:%M:%S",
        )

        if not trading_interval:
            continue

        _pk = set([trading_interval, record["REGIONID"]])

        if _pk in primary_keys:
            continue

        primary_keys.append(_pk)

        net_interchange = None

        if "NETINTERCHANGE" in record:
            net_interchange = clean_float(record["NETINTERCHANGE"])

        demand_total = None

        if "TOTALDEMAND" in record:
            demand_total = clean_float(record["TOTALDEMAND"])

        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": spider.name,
                "network_region": record["REGIONID"],
                "net_interchange_trading": net_interchange,
                "trading_interval": trading_interval,
                "demand_total": demand_total,
            }
        )

        records_processed += 1

        if limit and records_processed >= limit:
            logger.info("Reached limit of: {} {}".format(limit, records_processed))
            break

    stmt = insert(BalancingSummary).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "network_region"],
        set_={
            "demand_total": stmt.excluded.demand_total,
            "net_interchange_trading": stmt.excluded.net_interchange_trading,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        logger.error("Error inserting records")
        logger.error(e)
        return {"num_records": 0}

    finally:
        session.close()

    return {"num_records": len(records_to_store)}


def process_unit_scada(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = unit_scada_generate_facility_scada(
        table.records,
        interval_field="settlementdate",
        facility_code_field="duid",
        power_field="scadavalue",
    )

    cr.processed_records = len(records)
    cr.inserted_records = bulkinsert_mms_items(FacilityScada, records, ["generated"])

    return cr


def process_unit_solution(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = unit_scada_generate_facility_scada(
        table.records,
        interval_field="settlementdate",
        facility_code_field="duid",
        power_field="initialmw",
    )

    cr.processed_records = len(records)
    cr.inserted_records = bulkinsert_mms_items(FacilityScada, records, ["generated"])

    return cr


def process_meter_data_gen_duid(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = unit_scada_generate_facility_scada(
        table.records,
        interval_field="interval_datetime",
        facility_code_field="duid",
        power_field="mwh_reading",
    )

    cr.processed_records = len(records)
    cr.inserted_records = bulkinsert_mms_items(FacilityScada, records, ["generated"])

    return cr


def process_rooftop_actual(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = unit_scada_generate_facility_scada(
        table.records,
        interval_field="interval_datetime",
        facility_code_field="regionid",
        power_field="power",
    )

    cr.processed_records = len(records)
    cr.inserted_records = bulkinsert_mms_items(FacilityScada, records, ["generated"])

    return cr


def process_rooftop_forecase(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = unit_scada_generate_facility_scada(
        table.records,
        interval_field="interval_datetime",
        facility_code_field="regionid",
        power_field="powermean",
        is_forecast=True,
    )

    cr.processed_records = len(records)
    cr.inserted_records = bulkinsert_mms_items(FacilityScada, records, ["generated"])

    return cr


TABLE_PROCESSOR_MAP = {
    "dispatch_interconnectorres": "process_dispatch_interconnectorres",
    "dispatch_unit_scada": "process_unit_scada",
    "dispatch_unit_solution": "process_unit_solution",
    "meter_data_gen_duid": "process_meter_data_gen_duid",
    "rooftop_actual": "process_rooftop_actual",
    "rooftop_forecast": "process_rooftop_forecast",
    "dispatch_price": "process_nem_price",
    "trading_price": "process_nem_price",
    "dispatch_regionsum": "process_dispatch_regionsum",
    "trading_regionsum": "process_trading_regionsum",
}


def store_aemo_tableset(tableset: AEMOTableSet) -> List:
    if not tableset.tables:
        raise Exception("Invalid item - no tables located")

    ret = []

    for table in tableset.tables:
        if table.full_name not in TABLE_PROCESSOR_MAP:
            logger.info("No processor for table %s", table.full_name)
            continue

        process_meth = TABLE_PROCESSOR_MAP[table.full_name]

        if process_meth not in globals():
            logger.info("Invalid processing function %s", process_meth)
            continue

        logger.info("processing table {}".format(table.full_name))

        record_item = None

        record_item = globals()[process_meth](table)

        if record_item:
            ret.append(record_item)

    return ret
