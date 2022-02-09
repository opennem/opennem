"""WEM Controllers

Update facility intervals and balancing summary for WEM
"""
import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.clients.wem import WEMBalancingSummarySet, WEMFacilityIntervalSet
from opennem.controllers.schema import ControllerReturn
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BalancingSummary, FacilityScada

logger = logging.getLogger(__name__)


def store_wem_balancingsummary_set(balancing_set: WEMBalancingSummarySet) -> ControllerReturn:
    """Persist wem balancing set to the database"""
    engine = get_database_engine()
    session = SessionLocal()
    cr = ControllerReturn()

    records_to_store = []

    if not balancing_set.intervals:
        return cr

    cr.total_records = len(balancing_set.intervals)

    for _rec in balancing_set.intervals:
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
    stmt.bind = engine
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
        logger.error("Error: {}".format(e))
        cr.errors = len(records_to_store)
        cr.error_detail.append(str(e))
    finally:
        session.close()
        engine.dispose()

    return cr


def store_wem_facility_intervals(balancing_set: WEMFacilityIntervalSet) -> ControllerReturn:
    """Persist WEM facility intervals"""
    engine = get_database_engine()
    session = SessionLocal()
    cr = ControllerReturn()

    records_to_store = []

    if not balancing_set.intervals:
        return cr

    cr.total_records = len(balancing_set.intervals)

    for _rec in balancing_set.intervals:
        records_to_store.append(
            {
                "created_by": "wem.controller",
                "network_id": "WEM",
                "trading_interval": _rec.trading_interval,
                "facility_code": _rec.facility_code,
                "generated": _rec.generated,
                "eoi_quantity": _rec.eoi_quantity,
            }
        )
        cr.processed_records += 1

    if len(records_to_store) < 1:
        return cr

    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "facility_code", "is_forecast"],
        set_={
            "generated": stmt.excluded.generated,
            "eoi_quantity": stmt.excluded.eoi_quantity,
        },
    )

    try:
        session.execute(stmt)
        session.commit()
        cr.inserted_records = len(records_to_store)
    except Exception as e:
        logger.error("Error: {}".format(e))
        cr.errors = len(records_to_store)
        cr.error_detail.append(str(e))
    finally:
        session.close()
        engine.dispose()

    return cr
