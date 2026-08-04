"""WEM Controllers

Update facility intervals and balancing summary for WEM
"""

import logging

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from opennem.clients.wem import WEMBalancingSummarySet, WEMFacilityIntervalSet
from opennem.controllers.schema import ControllerReturn
from opennem.db import SessionLocal, get_database_engine, get_scoped_session
from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.utils.dates import get_today_nem

logger = logging.getLogger(__name__)

# asyncpg caps a statement at 32767 bind parameters. facility_scada inserts bind 7
# columns per row, so keep chunks well under that ceiling.
FACILITY_SCADA_INSERT_CHUNK_SIZE = 4000


def _chunk_records(records: list[dict], chunk_size: int = FACILITY_SCADA_INSERT_CHUNK_SIZE):
    """Yield records in chunks that fit within the postgres bind parameter limit"""
    for i in range(0, len(records), chunk_size):
        yield records[i : i + chunk_size]


def store_wem_balancingsummary_set(balancing_set: WEMBalancingSummarySet) -> ControllerReturn:
    """Persist wem balancing set to the database"""
    engine = get_database_engine()
    session = get_scoped_session()
    cr = ControllerReturn()

    records_to_store = []

    if not balancing_set.intervals:
        return cr

    cr.total_records = len(balancing_set.intervals)
    cr.server_latest = balancing_set.server_latest

    primary_keys = []

    for _rec in balancing_set.intervals:
        if not _rec.trading_day_interval:
            continue

        if (_rec.trading_day_interval) in primary_keys:
            continue

        primary_keys.append(_rec.trading_day_interval)

        records_to_store.append(
            {
                "created_by": "wem.controller",
                "trading_interval": _rec.trading_day_interval,
                "network_id": "WEM",
                "network_region": "WEM",
                "is_forecast": _rec.is_forecast,
                "forecast_load": _rec.forecast_mw,
                "generation_total": _rec.actual_total_generation,
                "generation_scheduled": _rec.actual_nsg_mw,
                "price": _rec.price,
            }
        )
        cr.processed_records += 1

    if len(records_to_store) < 1:
        return cr

    stmt = insert(BalancingSummary).values(records_to_store)
    stmt.bind = engine  # type: ignore
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            "trading_interval",
            "network_id",
            "network_region",
        ],
        set_={
            "price": stmt.excluded.price,
            "forecast_load": stmt.excluded.forecast_load,
            "generation_total": stmt.excluded.generation_total,
            "is_forecast": stmt.excluded.is_forecast,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
        cr.inserted_records = len(records_to_store)
    except Exception as e:
        logger.error(f"Error: {e}")
        cr.errors = len(records_to_store)
        cr.error_detail.append(str(e))
    finally:
        session.close()
        engine.dispose()

    return cr


async def store_wem_balancingsummary_set_bulk(balancing_set: WEMBalancingSummarySet) -> None:
    """Takes a lits of records and persists them to the database"""
    primary_keys = []
    records_to_store = []

    created_at = get_today_nem()

    for record in balancing_set.intervals:
        if not isinstance(record, dict):
            continue

        primary_key = {record.trading_day_interval}

        if primary_key in primary_keys:
            continue

        primary_keys.append(primary_key)

        if "DEMAND_AND_NONSCHEDGEN" not in record:
            raise Exception("bad value in dispatch_regionsum")

        records_to_store.append(
            {
                "created_by": "opennem.loader.dispatch_regionsum",
                "created_at": created_at,
                "updated_at": None,
                "network_id": "NEM",
                "trading_interval": record["TRADING_INTERVAL"],
                "forecast_load": None,
                "generation_scheduled": None,
                "generation_non_scheduled": None,
                "generation_total": None,
                "price": None,
                "network_region": record["REGIONID"],
                "is_forecast": False,
                "net_interchange": record["NETINTERCHANGE"],
                "demand_total": record["DEMAND_AND_NONSCHEDGEN"],
                "price_dispatch": None,
                "net_interchange_trading": None,
                "demand": record["TOTALDEMAND"],
            }
        )

    await bulkinsert_mms_items(BalancingSummary, records_to_store, ["net_interchange", "demand", "demand_total"])  # type: ignore

    return None


async def store_wem_facility_intervals(
    balancing_set: WEMFacilityIntervalSet, created_by: str = "wem.controller", fill_nulls_only: bool = False
) -> ControllerReturn:
    """Persist WEM facility intervals

    Args:
        fill_nulls_only: Only populate columns that are currently null, never overwrite an
            existing value. Used by the historical backfill so that re-ingesting a month
            which straddles the 2013-12-17 EOI cutover cannot clobber generation or energy
            that is already published.
    """
    cr = ControllerReturn()

    records_to_store = []

    if not balancing_set.intervals:
        return cr

    cr.total_records = len(balancing_set.intervals)
    cr.server_latest = balancing_set.server_latest

    primary_keys: set = set()

    for _rec in balancing_set.intervals:
        if (_rec.trading_interval, _rec.facility_code) in primary_keys:
            continue

        primary_keys.add((_rec.trading_interval, _rec.facility_code))

        records_to_store.append(
            {
                "network_id": "WEM",
                "interval": _rec.trading_interval.replace(tzinfo=None),
                "facility_code": _rec.facility_code,
                "generated": _rec.generated,
                "energy": _rec.energy,
                "is_forecast": False,
                "energy_quality_flag": 2,
            }
        )
        cr.processed_records += 1

    if len(records_to_store) < 1:
        return cr

    async with SessionLocal() as session:
        for chunk in _chunk_records(records_to_store):
            try:
                stmt = insert(FacilityScada).values(chunk)

                if fill_nulls_only:
                    set_ = {
                        "generated": func.coalesce(FacilityScada.generated, stmt.excluded.generated),
                        "energy": func.coalesce(FacilityScada.energy, stmt.excluded.energy),
                    }
                else:
                    set_ = {
                        "generated": stmt.excluded.generated,
                        "energy": stmt.excluded.energy,
                    }

                stmt = stmt.on_conflict_do_update(
                    index_elements=["interval", "network_id", "facility_code", "is_forecast"],
                    set_=set_,
                )

                await session.execute(stmt)
                await session.commit()
                cr.inserted_records += len(chunk)
            except Exception as e:
                logger.error(f"Error: {e}")
                cr.errors += len(chunk)
                # truncated: the driver echoes the entire parameterised statement
                cr.error_detail.append(str(e)[:500])
                await session.rollback()

        await session.close()

    return cr


async def store_wem_facility_intervals_bulk(facility_interval_set: WEMFacilityIntervalSet) -> ControllerReturn:
    """Persist WEM facility intervals

    Optimized bulk insert version
    """

    cr = ControllerReturn()

    records_to_store = []

    if not facility_interval_set.intervals:
        return cr

    cr.total_records = len(facility_interval_set.intervals)
    cr.server_latest = facility_interval_set.server_latest

    primary_keys: set = set()

    for _rec in facility_interval_set.intervals:
        if (_rec.trading_interval, _rec.facility_code) in primary_keys:
            continue

        primary_keys.add((_rec.trading_interval, _rec.facility_code))

        records_to_store.append(
            {
                "network_id": "WEM",
                "interval": _rec.trading_interval.replace(tzinfo=None),
                "facility_code": _rec.facility_code,
                "generated": _rec.generated,
                "energy": _rec.energy,
                "is_forecast": False,
                "energy_quality_flag": 2,
            }
        )

        cr.processed_records += 1

    if len(records_to_store) < 1:
        return cr

    await bulkinsert_mms_items(FacilityScada, records_to_store, ["generated", "energy"])  # type: ignore

    return cr
