"""OpenNEM Core Controller

Parses MMS tables into OpenNEM derived database
"""

import logging
from collections.abc import Hashable
from typing import Any

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from opennem.controllers.schema import ControllerReturn
from opennem.core.networks import NetworkNEM
from opennem.core.normalizers import clean_float
from opennem.core.parsers.aemo.mms import AEMOTableSchema, AEMOTableSet
from opennem.db import SessionLocal
from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.importer.rooftop import rooftop_remap_regionids
from opennem.schema.aemo.mms import MMSBaseClass
from opennem.schema.network import NetworkAEMORooftop, NetworkSchema
from opennem.utils.dates import parse_date

logger = logging.getLogger("opennem.controllers.nem")

# @TODO could read this from schema
FACILITY_SCADA_COLUMN_NAMES = [
    "network_id",
    "interval",
    "facility_code",
    "generated",
    "eoi_quantity",
    "is_forecast",
    "energy_quality_flag",
    "energy",
]

# Helpers


def generate_facility_scada(
    records: list[dict[str, Any] | MMSBaseClass],
    network: NetworkSchema = NetworkNEM,
    interval_field: str = "settlementdate",
    facility_code_field: str = "duid",
    power_field: str = "scadavalue",
    energy_field: str | None = None,
    is_forecast: bool = False,
) -> list[dict[Hashable, Any]]:
    """Optimized facility scada generator"""

    df = pd.DataFrame().from_records(records)

    column_renames = {
        interval_field: "interval",
        power_field: "generated",
        facility_code_field: "facility_code",
    }

    if energy_field:
        column_renames[energy_field] = "eoi_quantity"
    else:
        df["eoi_quantity"] = None

    df = df.rename(columns=column_renames)

    df["network_id"] = network.code
    df["is_forecast"] = is_forecast
    df["energy"] = 0
    df["energy_quality_flag"] = 0

    # cast dates
    df.interval = pd.to_datetime(df.interval)

    df.generated = pd.to_numeric(df.generated)
    df["generated"] = df["generated"].fillna(0)

    # fill in energies
    df["eoi_quantity"] = df.generated / (60 / network.interval_size)

    df = df[FACILITY_SCADA_COLUMN_NAMES]

    # set the index
    df.set_index(["interval", "network_id", "facility_code", "is_forecast"], inplace=True)

    # @NOTE optimized way to drop duplicates
    df = df[~df.index.duplicated(keep="last")]

    # records = df

    # reorder columns
    clean_records = df.reset_index(inplace=False)[FACILITY_SCADA_COLUMN_NAMES].to_dict("records")

    return clean_records


# Processors


async def process_dispatch_interconnectorres(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))
    records_to_store = []
    primary_keys = []

    for record in table.records:
        interval = parse_date(record["settlementdate"])

        if not interval:
            logger.warning(f"Invalid interval for record: {record}")
            continue

        interconnector_id = record.get("interconnectorid")

        if not interconnector_id:
            logger.warning(f"No interconnector id for record: {record}")
            continue

        primary_key = {interval, interconnector_id}

        if primary_key in primary_keys:
            continue

        primary_keys.append(primary_key)

        if "meteredmwflow" not in record:
            raise Exception(f"No meteredmwflow in record: {record}")

        records_to_store.append(
            {
                "network_id": "NEM",
                "facility_code": interconnector_id,
                "interval": interval,
                "generated": record.get("meteredmwflow", 0),
            }
        )
        cr.processed_records += 1

    # insert
    async with SessionLocal() as session:
        try:
            stmt = insert(FacilityScada).values(records_to_store)
            stmt = stmt.on_conflict_do_update(
                index_elements=["interval", "network_id", "facility_code", "is_forecast"],
                set_={"generated": stmt.excluded.generated},
            )

            await session.execute(stmt)
            await session.commit()

            cr.inserted_records = cr.processed_records
            cr.server_latest = max([r["interval"] for r in records_to_store]) if records_to_store else None
        except Exception as e:
            logger.error("Error inserting dispatch interconnectorres records")
            logger.error(e)
            cr.errors = cr.processed_records
            await session.rollback()
        finally:
            await session.close()

    return cr


async def process_nem_price(table: AEMOTableSchema) -> ControllerReturn:
    """Stores the NEM price for both dispatch price and trading price"""

    cr = ControllerReturn(total_records=len(table.records))
    records_to_store = []
    primary_keys = []

    price_field = "price"

    if table.full_name == "dispatch_price":
        price_field = "price_dispatch"

    for record in table.records:
        # @NOTE disable pk track
        interval = parse_date(record["settlementdate"])

        primary_key = {interval, record["regionid"]}

        if primary_key in primary_keys:
            continue

        primary_keys.append(primary_key)

        records_to_store.append(
            {
                "network_id": "NEM",
                "network_region": record.get("regionid"),
                "interval": interval,
                price_field: record["rrp"],
            }
        )

        cr.processed_records += 1

    async with SessionLocal() as session:
        try:
            stmt = insert(BalancingSummary).values(records_to_store)
            stmt = stmt.on_conflict_do_update(
                index_elements=["interval", "network_id", "network_region"],
                set_={price_field: getattr(stmt.excluded, price_field)},
            )

            await session.execute(stmt)
            await session.commit()

            cr.inserted_records = cr.processed_records
            cr.server_latest = max([r["interval"] for r in records_to_store]) if records_to_store else None
        except Exception as e:
            logger.error("Error inserting NEM price records")
            logger.error(e)
            cr.errors = cr.processed_records
            await session.rollback()
        finally:
            await session.close()

    return cr


async def process_dispatch_regionsum(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))
    records_to_store = []
    primary_keys = []

    for record in table.records:
        if not isinstance(record, dict):
            continue

        interval = parse_date(record.get("settlementdate"))

        primary_key = {interval, record["regionid"]}

        if primary_key in primary_keys:
            continue

        primary_keys.append(primary_key)

        if "demand_and_nonschedgen" not in record:
            raise Exception("bad value in dispatch_regionsum")

        records_to_store.append(
            {
                "network_id": "NEM",
                "network_region": record["regionid"],
                "interval": interval,
                "net_interchange": record["netinterchange"],
                "demand": record["totaldemand"],
                "demand_total": record["demand_and_nonschedgen"],
            }
        )

        cr.processed_records += 1

    async with SessionLocal() as session:
        try:
            stmt = insert(BalancingSummary).values(records_to_store)
            stmt = stmt.on_conflict_do_update(
                index_elements=["interval", "network_id", "network_region"],
                set_={
                    "net_interchange": stmt.excluded.net_interchange,
                    "demand_total": stmt.excluded.demand_total,
                    "demand": stmt.excluded.demand,
                },
            )

            await session.execute(stmt)
            await session.commit()

            cr.inserted_records = cr.processed_records
            cr.server_latest = max([r["interval"] for r in records_to_store]) if records_to_store else None
        except Exception as e:
            logger.error("Error inserting dispatch regionsum records")
            logger.error(e)
            cr.errors = cr.processed_records
            await session.rollback()
        finally:
            await session.close()

    return cr


async def process_trading_regionsum(table: AEMOTableSchema) -> ControllerReturn:
    """Process trading regionsum"""
    if not table.records:
        logger.debug(table)
        raise Exception("Invalid table no records")

    cr = ControllerReturn(total_records=len(table.records))
    limit = None
    records_to_store = []
    records_processed = 0
    primary_keys = []

    for record in table.records:
        if not isinstance(record, dict):
            raise Exception("Invalid record type")

        interval = parse_date(
            record["settlementdate"],
            network=NetworkNEM,
            dayfirst=False,
            date_format="%Y/%m/%d %H:%M:%S",
        )

        if not interval:
            continue

        _pk = {interval, record["regionid"]}

        if _pk in primary_keys:
            continue

        primary_keys.append(_pk)

        net_interchange = None

        if "netinterchange" in record:
            net_interchange = clean_float(record["netinterchange"])

        records_to_store.append(
            {
                "network_id": "NEM",
                "network_region": record["regionid"],
                "net_interchange_trading": net_interchange,
                "interval": interval,
            }
        )

        records_processed += 1

        if limit and records_processed >= limit:
            logger.info(f"Reached limit of: {limit} {records_processed}")
            break

    async with SessionLocal() as session:
        try:
            stmt = insert(BalancingSummary).values(records_to_store)
            stmt = stmt.on_conflict_do_update(
                index_elements=["interval", "network_id", "network_region"],
                set_={
                    "net_interchange_trading": stmt.excluded.net_interchange_trading,
                },
            )

            await session.execute(stmt)
            await session.commit()

            cr.inserted_records = records_processed
            cr.processed_records = records_processed
            cr.server_latest = max([i["interval"] for i in records_to_store]) if records_to_store else None
        except Exception as e:
            logger.error("Error inserting records")
            logger.error(e)
            cr.errors = records_processed
            await session.rollback()
        finally:
            await session.close()

    return cr


async def process_unit_scada_optimized(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = generate_facility_scada(
        table.records,  # type:ignore
        interval_field="settlementdate",
        facility_code_field="duid",
        power_field="scadavalue",
    )

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated", "eoi_quantity"])  # type: ignore
    cr.server_latest = max([i["interval"] for i in records if i["interval"]])

    return cr


async def process_unit_solution(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = generate_facility_scada(
        table.records,
        interval_field="settlementdate",
        facility_code_field="duid",
        power_field="initialmw",
    )

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated"])
    cr.server_latest = max([i["interval"] for i in records if i["interval"]])

    return cr


async def process_meter_data_gen_duid(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = generate_facility_scada(
        table.records,
        interval_field="interval_datetime",
        facility_code_field="duid",
        power_field="mwh_reading",
    )

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated"])
    cr.server_latest = max([i["interval"] for i in records])

    return cr


async def process_rooftop_actual(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = generate_facility_scada(
        table.records,
        interval_field="interval_datetime",
        facility_code_field="regionid",
        power_field="power",
        network=NetworkAEMORooftop,
    )

    records = [rooftop_remap_regionids(i) for i in records if i]
    records = [i for i in records if i]

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated", "eoi_quantity"])
    cr.server_latest = max([i["interval"] for i in records])

    return cr


async def process_rooftop_forecast(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = generate_facility_scada(
        table.records,  # type: ignore
        interval_field="interval_datetime",
        facility_code_field="regionid",
        power_field="powermean",
        is_forecast=True,
        network=NetworkAEMORooftop,
    )

    records = [rooftop_remap_regionids(i) for i in records if i]  # type: ignore
    records = [i for i in records if i]

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated"])  # type: ignore
    cr.server_latest = max([i["interval"] for i in records]) if records else None

    return cr


TABLE_PROCESSOR_MAP = {
    "dispatch_interconnectorres": "process_dispatch_interconnectorres",
    "dispatch_unit_scada": "process_unit_scada_optimized",
    "dispatch_unit_solution": "process_unit_solution",
    "meter_data_gen_duid": "process_meter_data_gen_duid",
    "rooftop_actual": "process_rooftop_actual",
    "rooftop_forecast": "process_rooftop_forecast",
    "dispatch_price": "process_nem_price",
    "trading_price": "process_nem_price",
    "dispatch_regionsum": "process_dispatch_regionsum",
    "trading_regionsum": "process_trading_regionsum",
}


async def store_aemo_tableset(tableset: AEMOTableSet) -> ControllerReturn:
    if not tableset.tables:
        raise Exception("Invalid item - no tables located")

    cr = ControllerReturn()

    for table in tableset.tables:
        if table.full_name not in TABLE_PROCESSOR_MAP:
            logger.info("No processor for table %s", table.full_name)
            continue

        process_meth = TABLE_PROCESSOR_MAP[table.full_name]

        if process_meth not in globals():
            logger.info("Invalid processing function %s", process_meth)
            continue

        logger.info(f"processing table {table.full_name} with {len(table.records)} records")

        record_item = None

        try:
            record_item = await globals()[process_meth](table)
            logger.info(f"Stored {record_item.inserted_records} records for table {table.full_name}")
        except Exception as e:
            logger.error(f"Error processing {table.full_name}: {e}")
            raise e

        if record_item:
            cr.processed_records += record_item.processed_records
            cr.total_records += record_item.total_records
            cr.inserted_records += record_item.inserted_records
            cr.errors += record_item.errors
            cr.error_detail += record_item.error_detail
            cr.server_latest = record_item.server_latest

    return cr
