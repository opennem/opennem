"""Persistence methods to facility_scada

"""
import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.controllers.schema import ControllerReturn
from opennem.db import get_database_engine, get_scoped_session
from opennem.db.bulk_insert_csv import bulkinsert_mms_items
from opennem.db.models.opennem import BalancingSummary, FacilityScada

from .schema import SchemaBalancingSummary, SchemaFacilityScada

logger = logging.getLogger(__name__)


def persist_postgres_facility_scada(records: list[SchemaFacilityScada]) -> int:
    """Persist WEM facility intervals"""
    engine = get_database_engine()
    session = get_scoped_session()
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


def persist_facility_scada_bulk(
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
