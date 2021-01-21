"""

NEMWEB Data ingress into OpenNEM format


"""

import logging
from datetime import datetime
from itertools import groupby
from typing import Any, Dict, List, Optional

from scrapy import Spider
from sqlalchemy.dialects.postgresql import insert

from opennem.core.networks import NetworkNEM
from opennem.core.normalizers import clean_float, normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BalancingSummary, Facility, FacilityScada
from opennem.importer.rooftop import rooftop_remap_regionids
from opennem.schema.network import NetworkSchema
from opennem.utils.dates import parse_date
from opennem.utils.numbers import float_to_str
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


# Helpers


def unit_scada_generate_facility_scada(
    records,
    spider=None,
    network: NetworkSchema = NetworkNEM,
    interval_field: str = "SETTLEMENTDATE",
    facility_code_field: str = "DUID",
    date_format: Optional[str] = None,
    power_field: Optional[str] = None,
    energy_field: Optional[str] = None,
    is_forecast: bool = False,
    primary_key_track: bool = False,
    groupby_filter: bool = True,
    created_by: str = None,
    limit: int = 0,
    duid: str = None,
) -> List[Dict]:
    created_at = datetime.now()
    primary_keys = []
    return_records = []

    created_by = ""

    if spider and hasattr(spider, "name"):
        created_by = spider.name

    for row in records:

        trading_interval = parse_date(
            row[interval_field],
            network=network,
            dayfirst=False,
            date_format=date_format,
        )

        # if facility_code_field not in row:
        # logger.error("Invalid row no facility_code")
        # continue

        facility_code = normalize_duid(row[facility_code_field])

        if duid and facility_code != duid:
            continue

        if primary_key_track:
            pkey = (trading_interval, facility_code)

            if pkey in primary_keys:
                continue

            primary_keys.append(pkey)

        generated = None

        if power_field and power_field in row:
            generated = clean_float(row[power_field])

            if generated:
                generated = float_to_str(generated)

        energy = None

        if energy_field and energy_field in row:
            energy = clean_float(row[energy_field])

            if energy:
                energy = float_to_str(energy)

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


def get_interconnector_facility(facility_code: str) -> Facility:
    session = SessionLocal()

    _fac = session.query(Facility).filter_by(code=facility_code).one_or_none()

    if not _fac:
        raise Exception("Could not find facility {}".format(facility_code))

    return _fac


def process_dispatch_interconnectorres(table: Dict, spider: Spider) -> Dict:
    session = SessionLocal()
    engine = get_database_engine()

    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]

    records_to_store = []

    for record in records:
        ti_value = None

        if "SETTLEMENTDATE" in record:
            ti_value = record["SETTLEMENTDATE"]

        if "RUN_DATETIME" in record:
            ti_value = record["RUN_DATETIME"]

        if not ti_value:
            raise Exception("Require a trading interval")

        trading_interval = parse_date(ti_value, network=NetworkNEM, dayfirst=False)

        if not trading_interval:
            continue

        facility_code = normalize_duid(record["INTERCONNECTORID"])
        power_value = clean_float(record["METEREDMWFLOW"])

        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": spider.name,
                "facility_code": facility_code,
                "trading_interval": trading_interval,
                "generated": power_value,
            }
        )

    # remove duplicates
    return_records_grouped = {}

    for pk_values, rec_value in groupby(
        records_to_store,
        key=lambda r: (
            r.get("trading_interval"),
            r.get("network_id"),
            r.get("facility_code"),
        ),
    ):
        if pk_values not in return_records_grouped:
            return_records_grouped[pk_values] = list(rec_value).pop()

    records_to_store = list(return_records_grouped.values())

    # insert
    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "facility_code"],
        set_={"generated": stmt.excluded.generated},
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


def process_case_solutions(table: Dict, spider: Spider):
    pass


def process_pre_ap_price(table: Dict, spider: Spider) -> Dict[str, Any]:
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

        price = None

        if "RRP" in record:
            price = clean_float(record["RRP"])

        records_to_store.append(
            {
                "network_id": "NEM",
                "created_by": spider.name,
                "network_region": record["REGIONID"],
                "trading_interval": trading_interval,
                # "price": record["PRE_AP_ENERGY_PRICE"],
                "price": price,
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
        set_={"price": stmt.excluded.price},
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


def process_dispatch_regionsum(table: Dict[str, Any], spider: Spider) -> Dict:
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
                "trading_interval": trading_interval,
                "net_interchange": net_interchange,
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
        return {"num_records": 0}

    finally:
        session.close()

    return {"num_records": len(records_to_store)}


def process_unit_scada(table: Dict[str, Any], spider: Spider) -> Dict:
    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]
    item = dict()

    item["table_schema"] = FacilityScada
    item["update_fields"] = ["generated"]
    item["records"] = unit_scada_generate_facility_scada(
        records,
        spider,
        power_field="SCADAVALUE",
        network=NetworkNEM,
        date_format="%Y/%m/%d %H:%M:%S",
    )
    item["content"] = ""

    return item


def process_unit_solution(table: Dict[str, Any], spider: Spider) -> Dict:
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


def process_meter_data_gen_duid(table: Dict[str, Any], spider: Spider) -> Dict:
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
        interval_field="INTERVAL_DATETIME",
        facility_code_field="DUID",
        power_field="MWH_READING",
    )
    item["content"] = None

    return item


def process_rooftop_actual(table: Dict[str, Any], spider: Spider) -> Dict:
    if "records" not in table:
        raise Exception("Invalid table no records")

    records = table["records"]
    item = dict()

    # Filter out for only measurements
    # as opposed to TYPE=SATELLITE
    records_filtered = list(filter(lambda x: x["TYPE"] == "MEASUREMENT", records))

    scada_records = unit_scada_generate_facility_scada(
        records_filtered,
        spider,
        network=NetworkNEM,
        interval_field="INTERVAL_DATETIME",
        facility_code_field="REGIONID",
        power_field="POWER",
        # don't filter down on duid since they'll conflict
        # we need to sum aggs
        groupby_filter=False,
    )

    scada_records = [rooftop_remap_regionids(i) for i in scada_records]
    return_records_grouped = {}

    # Merge and group
    for pk_values, rec_value in groupby(
        scada_records,
        key=lambda r: (
            r.get("facility_code"),
            r.get("network_id"),
            r.get("trading_interval"),
        ),
    ):
        if pk_values not in return_records_grouped:
            rec_values = list(rec_value)
            return_records_grouped[pk_values] = rec_values.pop()

            _cur_value = return_records_grouped[pk_values]["generated"]

            _cur_val = clean_float(_cur_value)

            if _cur_val:
                return_records_grouped[pk_values]["generated"] = _cur_val
            else:
                return_records_grouped[pk_values]["generated"] = 0.0

            for _rec in rec_values:
                _new_val = clean_float(_rec["generated"])

                if _new_val:
                    return_records_grouped[pk_values]["generated"] += _new_val

    return_records = list(return_records_grouped.values())

    item["table_schema"] = FacilityScada
    item["update_fields"] = ["generated"]
    item["records"] = return_records
    item["content"] = None

    return item


TABLE_PROCESSOR_MAP = {
    "DISPATCH_INTERCONNECTORRES": "process_dispatch_interconnectorres",
    # "P5MIN_INTERCONNECTORSOLN": "process_dispatch_interconnectorres",
    "METER_DATA_GEN_DUID": "process_meter_data_gen_duid",
    "DISPATCH_CASE_SOLUTION": "process_case_solutions",
    "DISPATCH_UNIT_SCADA": "process_unit_scada",
    "DISPATCH_UNIT_SOLUTION": "process_unit_solution",
    # "DISPATCH_PRE_AP_PRICE": "process_pre_ap_price",
    "ROOFTOP_ACTUAL": "process_rooftop_actual",
    "DISPATCH_PRICE": "process_pre_ap_price",
    "DISPATCH_REGIONSUM": "process_dispatch_regionsum",
}


class NemwebUnitScadaOpenNEMStorePipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if not item:
            msg = "NemwebUnitScadaOpenNEMStorePipeline"
            if spider and hasattr(spider, "name"):
                msg = spider.name
            logger.error("No item in pipeline: {}".format(msg))
            return {}

        if "tables" not in item:
            print(item)
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

            record_item = None

            try:
                record_item = globals()[process_meth](table, spider=spider)
            except Exception as e:
                logger.error(e)

            if record_item:
                ret.append(record_item)

        return ret
