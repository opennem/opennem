"""Persistence methods to facility_scada"""

import logging

import deprecation
from sqlalchemy.dialects.postgresql import insert

from opennem.controllers.schema import ControllerReturn
from opennem.db import SessionLocal, get_database_engine
from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary, FacilityScada
from opennem.utils.version import get_version

from .schema import BalancingSummarySchema, FacilityScadaSchema

logger = logging.getLogger(__name__)


@deprecation.deprecated(
    deprecated_in="4.0", removed_in="4.1", current_version=get_version(dev_tag=False), details="persist_facility_scada_bulk"
)
async def persist_postgres_facility_scada(records: list[FacilityScadaSchema]) -> int:
    """Persist WEM facility intervals"""
    engine = get_database_engine()
    cr = ControllerReturn()

    records_to_store = [dict(i) for i in records]

    stmt = insert(FacilityScada).values(records_to_store)
    stmt.bind = engine  # type: ignore
    stmt = stmt.on_conflict_do_update(
        index_elements=["interval", "network_id", "facility_code", "is_forecast"],
        set_={
            "generated": stmt.excluded.generated,
        },
    )

    async with SessionLocal() as session:
        try:
            await session.execute(stmt)
            await session.commit()
            cr.inserted_records = len(records_to_store)
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            await session.close()
            await engine.dispose()

    return len(records_to_store)


async def persist_facility_scada_bulk(
    records: list[FacilityScadaSchema | BalancingSummarySchema], update_fields: list[str] | None = None
) -> None:
    """Takes a lits of records and persists them to the database"""

    records_to_store = [dict(i) for i in records]

    if not update_fields:
        update_fields = ["interval", "network_id", "facility_code", "is_forecast"]

    table = FacilityScada

    if isinstance(records[0], BalancingSummarySchema):
        table = BalancingSummary

    await bulkinsert_mms_items(table=table, records=records_to_store, update_fields=update_fields)  # type: ignore

    return None
