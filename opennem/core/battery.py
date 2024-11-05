"""
OpenNEM Battery Module

This will split bidirectional batteries into two separate entities, one for charging and one for discharging.

It is called from the NEM crawl controller.

"""

import logging
from dataclasses import dataclass

from sqlalchemy import select, text

from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import Facility, Unit
from opennem.schema.unit import UnitDispatchType, UnitSchema

logger = logging.getLogger("opennem.core.battery")


@dataclass
class BatteryUnitMap:
    unit: UnitSchema
    charge_unit: UnitSchema
    discharge_unit: UnitSchema


UNIT_MAP: dict[str, BatteryUnitMap] = {}


async def get_battery_unit_map() -> dict[str, BatteryUnitMap]:
    """This queries the database for all the bidirectional battery units and returns what each should be mapped to"""

    async with get_read_session() as session:
        facility_query = await session.execute(
            select(Facility)
            .join(Unit)
            .where(Unit.dispatch_type == UnitDispatchType.BIDIRECTIONAL.value)
            .order_by(Facility.code, Unit.code)
        )
        facilities = facility_query.scalars().all()

        logger.debug(f"Found {len(facilities)} bidirectional units")

        for facility in facilities:
            # find the bidirectional unit
            bidirectional_unit = next(
                (unit for unit in facility.units if unit.dispatch_type == UnitDispatchType.BIDIRECTIONAL.value), None
            )

            if not bidirectional_unit:
                logger.warning(f"No bidirectional unit found for {facility.code} {facility.name}")
                continue

            unit_schema = UnitSchema(
                **bidirectional_unit.__dict__,
            )

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
                logger.warning(
                    f"Multiple charge units found for {facility.code} {facility.name}: {",".join([i.code for i in charge_unit])}"
                )
                continue

            if len(discharge_unit) > 1:
                logger.warning(f"Multiple discharge units found for {facility.code} {facility.name}: {",".join(discharge_unit)}")
                continue

            charge_unit_schema = UnitSchema(**charge_unit[0].__dict__)
            discharge_unit_schema = UnitSchema(**discharge_unit[0].__dict__)

            UNIT_MAP[bidirectional_unit.code] = BatteryUnitMap(
                unit=unit_schema,
                charge_unit=charge_unit_schema,
                discharge_unit=discharge_unit_schema,
            )

            # create the charge and discharge units

    return UNIT_MAP


async def process_battery_history():
    """This processes the history of facility_scada and updates the battery units so that
    bidirectional units are split into two separate units
    """
    unit_map = await get_battery_unit_map()

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
        for unit_map in unit_map.values():  # type: ignore  # noqa: B020
            # clear out old records
            result = await session.execute(
                text(
                    "delete from facility_scada where facility_code in (:discharge_facility_code, :charge_facility_code) "
                    "and interval >= (select min(interval) from facility_scada where facility_code=:bidirectional_facility_code);"
                ),
                {
                    "discharge_facility_code": unit_map.discharge_unit.code,
                    "charge_facility_code": unit_map.charge_unit.code,
                    "bidirectional_facility_code": unit_map.unit.code,
                },
            )

            logger.info(
                f"Deleted {unit_map.discharge_unit.code} and {unit_map.charge_unit.code} records newer than "
                f"{unit_map.unit.code}: {result.rowcount}"  # type: ignore
            )

            await session.execute(
                query_load_template,
                {"new_facility_code": unit_map.charge_unit.code, "old_facility_code": unit_map.unit.code},
            )

            logger.info(f"Updated {unit_map.unit.code} charge to {unit_map.charge_unit.code}")
            await session.execute(
                query_generator,
                {"new_facility_code": unit_map.discharge_unit.code, "old_facility_code": unit_map.unit.code},
            )

            logger.info(f"Updated {unit_map.unit.code} discharge to {unit_map.discharge_unit.code}")

            await session.commit()


if __name__ == "__main__":
    import asyncio

    unit_map = asyncio.run(process_battery_history())

    from pprint import pprint

    pprint(unit_map)
