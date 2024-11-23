"""
OpenNEM Battery Module

This will split bidirectional batteries into two separate entities, one for charging and one for discharging.

It is called from the NEM crawl controller.

"""

import logging

from pydantic import BaseModel
from sqlalchemy import select, text

from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import Facility, Unit
from opennem.schema.field_types import DUIDType
from opennem.schema.unit import UnitDispatchType, UnitSchema

logger = logging.getLogger("opennem.core.battery")


class BatteryUnitMap(BaseModel):
    unit: DUIDType
    charge_unit: DUIDType
    discharge_unit: DUIDType


UNIT_MAP: dict[DUIDType, BatteryUnitMap] = {}


async def get_battery_unit_map() -> dict[str, BatteryUnitMap]:
    """Get the battery unit mapping, generating it if not already cached.

    Returns:
        dict[str, BatteryUnitMap]: Mapping of bidirectional unit codes to their charge/discharge units
    """
    global UNIT_MAP
    if not UNIT_MAP:
        UNIT_MAP = await _generate_battery_unit_map()
    return UNIT_MAP


async def _generate_battery_unit_map(facility_code: str | None = None) -> dict[str, BatteryUnitMap]:
    """This queries the database for all the bidirectional battery units and returns what each should be mapped to"""

    async with get_read_session() as session:
        facility_query = select(Facility).join(Unit).where(Unit.dispatch_type == UnitDispatchType.BIDIRECTIONAL.value)

        if facility_code:
            facility_query = facility_query.where(Facility.code == facility_code)

        facility_query = facility_query.order_by(Facility.code, Unit.code)

        facilities = (await session.execute(facility_query)).scalars().all()

        logger.debug(f"Found {len(facilities)} bidirectional units")

        for facility in facilities:
            # find the bidirectional unit
            bidirectional_unit = next(
                (unit for unit in facility.units if unit.dispatch_type == UnitDispatchType.BIDIRECTIONAL.value), None
            )

            if not bidirectional_unit:
                logger.warning(f"No bidirectional unit found for {facility.code} {facility.name}")
                continue

            # find the charge and discharge units
            charge_unit = list(filter(lambda x: x.fueltech_id == "battery_charging", facility.units))
            discharge_unit = list(filter(lambda x: x.fueltech_id == "battery_discharging", facility.units))

            if not charge_unit:
                logger.warning(f"No charge unit found for {facility.code} {facility.name}")
                continue

            if not discharge_unit:
                logger.warning(f"No discharge unit found for {facility.code} {facility.name}")
                continue

            if len(charge_unit) > 1:
                logger.warning(f"Multiple charge units found for {facility.code} {facility.name}")
                continue

            if len(discharge_unit) > 1:
                logger.warning(f"Multiple discharge units found for {facility.code} {facility.name}")
                continue

            charge_unit_schema = UnitSchema(**charge_unit[0].__dict__)
            discharge_unit_schema = UnitSchema(**discharge_unit[0].__dict__)

            UNIT_MAP[str(bidirectional_unit.code)] = BatteryUnitMap(
                unit=str(bidirectional_unit.code),
                charge_unit=charge_unit_schema.code,
                discharge_unit=discharge_unit_schema.code,
            )

            # create the charge and discharge units

    return UNIT_MAP


async def process_battery_history(facility_code: str | None = None):
    """This processes the history of facility_scada and updates the battery units so that
    bidirectional units are split into two separate units
    """
    unit_map = await _generate_battery_unit_map(facility_code=facility_code)

    query_load_template = text(
        "update facility_scada set facility_code = :new_facility_code where facility_code = :old_facility_code "
        "and generated < 0 "
        # "on conflict (network_id, interval, facility_code, is_forecast) do nothing"
    )

    query_generator = text(
        "update facility_scada set facility_code = :new_facility_code where facility_code = :old_facility_code "
        "and generated >= 0 "
        # "on conflict (network_id, interval, facility_code, is_forecast) do nothing "
    )

    async with get_write_session() as session:
        for unit in unit_map.values():  # type: ignore  # noqa: B020
            # clear out old records
            result = await session.execute(
                text(
                    "delete from facility_scada where facility_code in (:discharge_facility_code, :charge_facility_code) "
                    "and interval >= (select min(interval) from facility_scada where facility_code=:bidirectional_facility_code);"
                ),
                {
                    "discharge_facility_code": unit.discharge_unit,
                    "charge_facility_code": unit.charge_unit,
                    "bidirectional_facility_code": unit.unit,
                },
            )

            logger.info(
                f"Deleted {unit.discharge_unit} and {unit.charge_unit} records newer than " f"{unit.unit}: {result.rowcount}"  # type: ignore
            )

            await session.execute(
                query_load_template,
                {"new_facility_code": unit.charge_unit, "old_facility_code": unit.unit},
            )

            logger.info(f"Updated {unit.unit} charge to {unit.charge_unit}")
            await session.execute(
                query_generator,
                {"new_facility_code": unit.discharge_unit, "old_facility_code": unit.unit},
            )

            logger.info(f"Updated {unit.unit} discharge to {unit.discharge_unit}")

        await session.commit()


if __name__ == "__main__":
    import asyncio

    unit_map = asyncio.run(process_battery_history(facility_code="KWINANA_ESR"))

    # for unit in unit_map.values():
    #     print(f"{unit.unit} -> {unit.charge_unit} | {unit.discharge_unit}")
