"""APVI Controllers

Update facility intervals for APVI rooftop data, update capacities
and various other methods for persisting APVI data
"""

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from opennem.clients.apvi import APVIForecastSet
from opennem.controllers.schema import ControllerReturn
from opennem.db import SessionLocal, db_connect
from opennem.db.models.opennem import Facility, FacilityScada

logger = logging.getLogger(__name__)


async def store_apvi_forecastset(forecast_set: APVIForecastSet) -> ControllerReturn:
    """Persist an APVI forecast set to the database"""
    engine = db_connect()
    cr = ControllerReturn()

    records_to_store = []

    if not forecast_set.intervals:
        return cr

    cr.total_records = len(forecast_set.intervals)

    for _rec in forecast_set.intervals:
        records_to_store.append({**_rec.dict(exclude={"state"}), "is_forecast": False})
        cr.processed_records += 1

    if not records_to_store:
        return cr

    async with SessionLocal() as session:
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
            await session.execute(stmt)
            await session.commit()
            cr.inserted_records = len(records_to_store)
        except Exception as e:
            logger.error(f"Error: {e}")
            cr.errors = len(records_to_store)
            cr.error_detail.append(str(e))

    return cr


async def update_apvi_facility_capacities(forecast_set: APVIForecastSet) -> None:
    """Updates facility capacities for APVI rooftops"""

    if not forecast_set.capacities:
        return None

    async with SessionLocal() as session:
        for state_capacity in forecast_set.capacities:
            stmt = (
                select(Facility)
                .options(selectinload(Facility.network))  # Add any other relationships you need to load
                .filter_by(code=state_capacity.facility_code)
            )
            result = await session.execute(stmt)
            state_facility: Facility | None = result.unique().scalar_one_or_none()

            if not state_facility:
                logger.warning(f"Could not find rooftop facility for {state_capacity.facility_code}")
                continue

            state_facility.capacity_registered = state_capacity.capacity_registered
            state_facility.unit_number = state_capacity.unit_number

            session.add(state_facility)

        await session.commit()

    logger.info(f"Updated {len(forecast_set.capacities)} facility capacities")
