"""Persistence methods to facility_scada"""

import logging

from numpy import deprecate
from sqlalchemy.dialects.postgresql import insert

from opennem.controllers.schema import ControllerReturn
from opennem.db import SessionLocal, get_database_engine
from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary, FacilityScada

from .schema import SchemaBalancingSummary, SchemaFacilityScada

logger = logging.getLogger(__name__)


@deprecate(message="Use async persist_facility_scada_bulk instead")
async def persist_postgres_facility_scada(records: list[SchemaFacilityScada]) -> int:
    """Persist WEM facility intervals"""
    engine = get_database_engine()
    cr = ControllerReturn()

    records_to_store = [dict(i) for i in records]

    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine
    stmt = stmt.on_conflict_do_update(
        index_elements=["trading_interval", "network_id", "facility_code", "is_forecast"],
        set_={
            "generated": stmt.excluded.generated,
        },
    )

    async with SessionLocal() as session:
        try:
            session.execute(stmt)
            session.commit()
            cr.inserted_records = len(records_to_store)
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            session.close()
            engine.dispose()

    return len(records_to_store)


async def persist_facility_scada_bulk(
    records: list[SchemaFacilityScada | SchemaBalancingSummary], update_fields: list[str] | None = None
) -> None:
    """Takes a lits of records and persists them to the database"""

    records_to_store = [dict(i) for i in records]

    if not update_fields:
        update_fields = ["trading_interval", "network_id", "facility_code", "is_forecast"]

    table = FacilityScada

    if isinstance(records[0], SchemaBalancingSummary):
        table = BalancingSummary

    bulkinsert_mms_items(table=table, records=records_to_store, update_fields=update_fields)  # type: ignore

    return None
