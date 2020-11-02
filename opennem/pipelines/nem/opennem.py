"""

NEMWEB Data ingress into OpenNEM format


"""

import logging
from collections import OrderedDict
from datetime import datetime
from itertools import groupby
from typing import Dict, List, Optional

from sqlalchemy.dialects.postgresql import insert

from opennem.core.networks import NetworkNEM
from opennem.core.normalizers import clean_float, normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.schema.network import NetworkSchema
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def process_case_solutions(table):
    pass


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
        index_elements=["trading_interval", "network_id", "network_region"],
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


def unit_scada_generate_facility_scada(
    records,
    spider=None,
    network: NetworkSchema = NetworkNEM,
    interval_field: str = "SETTLEMENTDATE",
    facility_code_field: str = "DUID",
    power_field: Optional[str] = None,
    energy_field: Optional[str] = None,
    is_forecast: bool = False,
    primary_key_track: bool = False,
    groupby_filter: bool = True,
    created_by: str = None,
    limit: int = 0,
) -> List[Dict]:
    created_at = datetime.now()
    primary_keys = []
    return_records = []

    created_by = ""

    if spider and hasattr(spider, "name"):
        created_by = spider.name

    for row in records:

        trading_interval = parse_date(
            row[interval_field], network=network, dayfirst=False
        )

        # if facility_code_field not in row:
        # logger.error("Invalid row no facility_code")
        # continue

        facility_code = normalize_duid(row[facility_code_field])

        if primary_key_track:
            pkey = (trading_interval, facility_code)

            if pkey in primary_keys:
                continue

            primary_keys.append(pkey)

        generated = None

        if power_field and power_field in row:
            generated = clean_float(row[power_field])

        energy = None

        if energy_field and energy_field in row:
            energy = clean_float(row[energy_field])

        __rec = {
            "created_by": created_by,
            "created_at": created_at,
            "updated_at": None,
            "network_id": network.code,
            "trading_interval": trading_interval,
            "facility_code": facility_code,
            "generated": generated,
            "eoi_quantity": energy,
            "is_forecast": is_forecast,
        }

        return_records.append(__rec)

        if limit > 0 and len(return_records) >= limit:
            break

    if not groupby_filter:
        return return_records

    return_records_grouped = {}

    for pk_values, rec_value in groupby(
        return_records,
        key=lambda r: (
            r.get("network_id"),
            r.get("trading_interval"),
            r.get("facility_code"),
        ),
    ):
        if pk_values not in return_records_grouped:
            return_records_grouped[pk_values] = list(rec_value).pop()

    return_records = list(return_records_grouped.values())

    return return_records


def process_unit_scada(table, spider):
    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]
    item = dict()

    item["table_schema"] = FacilityScada
    item["update_fields"] = ["generated"]
    item["records"] = unit_scada_generate_facility_scada(
        records, spider, power_field="SCADAVALUE", network=NetworkNEM
    )
    item["content"] = None

    return item


def process_unit_solution(table, spider):
    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]
    item = dict()

    item["table_schema"] = FacilityScada
    item["update_fields"] = ["generated"]
    item["records"] = unit_scada_generate_facility_scada(
        records,
        spider,
        network=NetworkNEM,
        interval_field="SETTLEMENTDATE",
        facility_code_field="DUID",
        power_field="INITIALMW",
    )
    item["content"] = None

    return item


def process_meter_data_gen_duid(table, spider):
    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]
    item = dict()

    item["table_schema"] = FacilityScada
    item["update_fields"] = ["eoi_generated"]
    item["records"] = unit_scada_generate_facility_scada(
        records,
        spider,
        network=NetworkNEM,
        interval_field="INTERVAL_DATETIME",
        facility_code_field="DUID",
        energy_field="MWH_READING",
    )
    item["content"] = None

    return item


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
            raise Exception("Invalid item - no tables located")

        if not isinstance(item["tables"], dict):
            raise Exception("Invalid item - no tables located")

        tables = item["tables"]

        ret = []

        for table in tables.values():
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

            logger.info("processing table {}".format(table_name))
            record_item = globals()[process_meth](table, spider=spider)

            ret.append(record_item)

        return ret
