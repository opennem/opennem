"""OpenNEM Core Controller

Parses MMS tables into OpenNEM derived database
"""

import logging
from collections.abc import Hashable
from datetime import timedelta
from typing import Any

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from opennem.controllers.schema import ControllerReturn
from opennem.core.battery import get_battery_unit_map
from opennem.core.networks import NetworkNEM
from opennem.core.normalizers import clean_float
from opennem.core.parsers.aemo.mms import AEMOTableSchema, AEMOTableSet
from opennem.db import get_write_session
from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.importer.rooftop import rooftop_remap_regionids
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
    "energy_storage",
]

# Helpers


async def generate_facility_scada(
    records: list[dict[str, Any]],
    network: NetworkSchema = NetworkNEM,
    interval_field: str = "settlementdate",
    facility_code_field: str = "duid",
    power_field: str = "scadavalue",
    energy_field: str | None = None,
    energy_storage_field: str | None = None,
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
        column_renames[energy_field] = "energy"
    else:
        df["energy"] = None

    if energy_storage_field:
        column_renames[energy_storage_field] = "energy_storage"
    else:
        df["energy_storage"] = None

    df = df.rename(columns=column_renames)

    df["network_id"] = network.code
    df["is_forecast"] = is_forecast
    df["eoi_quantity"] = None
    df["energy_quality_flag"] = 0

    # cast dates
    df.interval = pd.to_datetime(df.interval)

    df.generated = pd.to_numeric(df.generated)
    df["generated"] = df["generated"].fillna(0)

    df = df[FACILITY_SCADA_COLUMN_NAMES]

    # Get battery unit mappings
    battery_unit_map = await get_battery_unit_map()

    def is_battery_unit(row) -> bool:
        facility_code = row["facility_code"]
        return facility_code in battery_unit_map

    # Create copies of battery records for splitting
    battery_mask = df.apply(is_battery_unit, axis=1)
    battery_copies = df.loc[battery_mask].copy()
    battery_copies["battery_copy"] = True

    # Add battery_copy field to original data (False for all)
    df["battery_copy"] = False

    # Combine original data with battery copies
    if len(battery_copies) > 0:
        df = pd.concat([df, battery_copies], ignore_index=True)

    # Define the original mapping functions
    def map_battery_code(row):
        facility_code = row["facility_code"]
        generated = row["generated"]

        if facility_code in battery_unit_map:
            battery_map = battery_unit_map[facility_code]
            if generated < 0:
                return battery_map.charge_unit
            else:
                return battery_map.discharge_unit
        return facility_code

    def map_battery_generation(row):
        facility_code = row["facility_code"]
        generated = row["generated"]

        for _, battery_map in battery_unit_map.items():
            if facility_code == battery_map.charge_unit:
                return abs(generated)

        return generated

    # Apply the mapping functions only to the battery copies
    battery_copy_mask = df["battery_copy"]
    df.loc[battery_copy_mask, "facility_code"] = df.loc[battery_copy_mask].apply(map_battery_code, axis=1)
    df.loc[battery_copy_mask, "generated"] = df.loc[battery_copy_mask].apply(map_battery_generation, axis=1)

    # Drop the battery_copy field
    df = df.drop(columns=["battery_copy"])

    # fill in energies
    df["energy"] = df.generated / (60 / network.interval_size)

    # set the index
    df.set_index(["interval", "network_id", "facility_code", "is_forecast"], inplace=True)

    # @NOTE optimized way to drop duplicates
    df_deduped: pd.DataFrame = df[~df.index.duplicated(keep="last")]  # type: ignore

    # reorder columns
    df_reset = df_deduped.reset_index(inplace=False)  # type: ignore
    df_final = df_reset[FACILITY_SCADA_COLUMN_NAMES]  # type: ignore
    clean_records = df_final.to_dict("records")  # type: ignore

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
    async with get_write_session() as session:
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

    # Process records in chunks
    chunk_size = 1000
    for i in range(0, len(records_to_store), chunk_size):
        chunk = records_to_store[i : i + chunk_size]

        async with get_write_session() as session:
            try:
                stmt = insert(BalancingSummary).values(chunk)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["interval", "network_id", "network_region", "is_forecast"],
                    set_={price_field: getattr(stmt.excluded, price_field)},
                )

                await session.execute(stmt)
                await session.commit()

                cr.inserted_records += len(chunk)

                logger.debug(f"Inserted {len(chunk)} records for NEM price")
            except Exception as e:
                logger.error(f"Error inserting NEM price records (chunk {i // chunk_size + 1})")
                logger.error(e)
                cr.errors += len(chunk)
                await session.rollback()
            finally:
                await session.close()

    cr.server_latest = max([r["interval"] for r in records_to_store]) if records_to_store else None

    return cr


async def process_dispatch_regionsum(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))
    records_to_store = []
    primary_keys = []

    for record in table.records:
        if not isinstance(record, dict):
            continue

        interval = parse_date(record.get("settlementdate"))

        if not interval:
            continue

        # get the next interval
        interval_next = interval + timedelta(minutes=5)

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

        # curtailment data needs to be shifted forward 5 minutes. See issue 455
        # https://github.com/opennem/opennem/issues/455
        records_to_store.append(
            {
                "network_id": "NEM",
                "network_region": record["regionid"],
                "interval": interval_next,
                "ss_solar_uigf": record["ss_solar_uigf"],
                "ss_solar_clearedmw": record["ss_solar_clearedmw"],
                "ss_wind_uigf": record["ss_wind_uigf"],
                "ss_wind_clearedmw": record["ss_wind_clearedmw"],
            }
        )

        cr.processed_records += 2

    async with get_write_session() as session:
        try:
            stmt = insert(BalancingSummary).values(records_to_store)
            stmt = stmt.on_conflict_do_update(
                index_elements=["interval", "network_id", "network_region", "is_forecast"],
                set_={
                    "net_interchange": stmt.excluded.net_interchange,
                    "demand_total": stmt.excluded.demand_total,
                    "demand": stmt.excluded.demand,
                    "ss_solar_uigf": stmt.excluded.ss_solar_uigf,
                    "ss_solar_clearedmw": stmt.excluded.ss_solar_clearedmw,
                    "ss_wind_uigf": stmt.excluded.ss_wind_uigf,
                    "ss_wind_clearedmw": stmt.excluded.ss_wind_clearedmw,
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

    async with get_write_session() as session:
        try:
            stmt = insert(BalancingSummary).values(records_to_store)
            stmt = stmt.on_conflict_do_update(
                index_elements=["interval", "network_id", "network_region", "is_forecast"],
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

    records = await generate_facility_scada(
        table.records,  # type:ignore
        interval_field="settlementdate",
        facility_code_field="duid",
        power_field="scadavalue",
    )

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated", "energy"])  # type: ignore
    cr.server_latest = max([i["interval"] for i in records if i["interval"]])

    return cr


async def process_unit_solution(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = await generate_facility_scada(
        table.records,  # type: ignore
        interval_field="settlementdate",
        facility_code_field="duid",
        power_field="initialmw",
        energy_storage_field="energy_storage",
    )

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated", "energy", "energy_storage"])
    cr.server_latest = max([i["interval"] for i in records if i["interval"]])

    return cr


async def process_meter_data_gen_duid(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = await generate_facility_scada(
        table.records,  # type: ignore
        interval_field="interval_datetime",
        facility_code_field="duid",
        power_field="mwh_reading",
    )

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated", "energy"])
    cr.server_latest = max([i["interval"] for i in records])

    return cr


async def process_rooftop_actual(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = await generate_facility_scada(
        table.records,  # type: ignore
        interval_field="interval_datetime",
        facility_code_field="regionid",
        power_field="power",
        network=NetworkAEMORooftop,
    )

    records = [rooftop_remap_regionids(i) for i in records if i]
    records = [i for i in records if i]

    cr.processed_records = len(records)
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated", "energy"])
    cr.server_latest = max([i["interval"] for i in records])

    return cr


async def process_rooftop_forecast(table: AEMOTableSchema) -> ControllerReturn:
    cr = ControllerReturn(total_records=len(table.records))

    records = await generate_facility_scada(
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
    cr.inserted_records = await bulkinsert_mms_items(FacilityScada, records, ["generated", "energy"])  # type: ignore
    cr.server_latest = max([i["interval"] for i in records]) if records else None

    return cr


_TABLE_PROCESSOR_MAP = {
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
        if table.full_name not in _TABLE_PROCESSOR_MAP:
            logger.debug("No processor for table %s", table.full_name)
            continue

        process_meth = _TABLE_PROCESSOR_MAP[table.full_name]

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

    logger.info(f"Stored {cr.inserted_records} records of {cr.total_records} in {len(tableset.tables)} tables")

    return cr
