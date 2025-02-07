"""
OpenNEM Battery Module

This will split bidirectional batteries into two separate entities, one for charging and one for discharging.

It is called from the NEM crawl controller.

"""

import logging

from pydantic import BaseModel
from sqlalchemy import select, text

from opennem import settings
from opennem.clients.slack import slack_message
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


def _generate_manual_battery_unit_map() -> dict[str, BatteryUnitMap]:
    """This is a manual map of bidirectional units to their charge/discharge units"""
    return {"COLLIE_ESR1": BatteryUnitMap(unit="COLLIE_ESR1", charge_unit="COLLIE_ESRL1", discharge_unit="COLLIE_ESRG1")}


async def _generate_battery_unit_map() -> dict[str, BatteryUnitMap]:
    """This queries the database for all the bidirectional battery units and returns what each should be mapped to"""

    # if we have a manual map start with that
    unit_map: dict[str, BatteryUnitMap] = _generate_manual_battery_unit_map()

    async with get_read_session() as session:
        facility_query = select(Facility).join(Unit).where(Unit.dispatch_type == UnitDispatchType.BIDIRECTIONAL.value)

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

            if unit_map.get(str(bidirectional_unit.code)):
                logger.info(f"Skipping {facility.code} {facility.name} as it has a manual or existing map")
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

            unit_map[str(bidirectional_unit.code)] = BatteryUnitMap(
                unit=str(bidirectional_unit.code),
                charge_unit=charge_unit_schema.code,
                discharge_unit=discharge_unit_schema.code,
            )

            # create the charge and discharge units

    return unit_map


async def process_battery_history(facility_code: str | None = None, clear_old_records: bool = False):
    """This processes the history of facility_scada and updates the battery units so that
    bidirectional units are split into two separate units
    """
    unit_map = await get_battery_unit_map()

    if not unit_map.get(facility_code):
        logger.warning(f"No unit map found for {facility_code}")
        return

    if facility_code:
        unit_map = {facility_code: unit_map[facility_code]}

    query_load_template = text(
        """
        WITH source AS (
            SELECT interval, network_id, facility_code, abs(generated) as generated, abs(energy) as energy,
                   is_forecast, energy_quality_flag
            FROM facility_scada
            WHERE facility_code = :old_facility_code AND generated < 0
        )
        INSERT INTO facility_scada (interval, network_id, facility_code, generated, energy, is_forecast, energy_quality_flag)
        SELECT s.interval, s.network_id, :new_facility_code, s.generated, s.energy, s.is_forecast, s.energy_quality_flag
        FROM source s
        ON CONFLICT (interval, network_id, facility_code, is_forecast) DO UPDATE
        SET generated = EXCLUDED.generated,
            energy = EXCLUDED.energy,
            energy_quality_flag = EXCLUDED.energy_quality_flag
        """
    )

    query_load_delete = text(
        """
        DELETE FROM facility_scada
        WHERE facility_code = :old_facility_code
        AND generated < 0
        """
    )

    query_load_aggregate_template = text(
        """
        WITH source AS (
            SELECT interval, network_id, facility_code, unit_code, fueltech_code, network_region, status_id,
                   abs(generated) as generated, abs(energy) as energy, emissions, emissions_intensity, market_value
            FROM at_facility_intervals
            WHERE unit_code = :old_facility_code AND generated < 0
        )
        INSERT INTO at_facility_intervals (
            interval, network_id, facility_code, unit_code, fueltech_code, network_region, status_id,
            generated, energy, emissions, emissions_intensity, market_value
        )
        SELECT s.interval, s.network_id, s.facility_code, :new_facility_code, s.fueltech_code, s.network_region, s.status_id,
               s.generated, s.energy, s.emissions, s.emissions_intensity, s.market_value
        FROM source s
        ON CONFLICT (interval, network_id, facility_code, unit_code) DO UPDATE
        SET generated = EXCLUDED.generated,
            energy = EXCLUDED.energy,
            emissions = EXCLUDED.emissions,
            emissions_intensity = EXCLUDED.emissions_intensity,
            market_value = EXCLUDED.market_value
        """
    )

    query_load_aggregate_delete = text(
        """
        DELETE FROM at_facility_intervals
        WHERE unit_code = :old_facility_code
        AND generated < 0
        """
    )

    query_generator = text(
        """
        WITH source AS (
            SELECT interval, network_id, facility_code, generated, energy, is_forecast, energy_quality_flag
            FROM facility_scada
            WHERE facility_code = :old_facility_code AND generated >= 0
        )
        INSERT INTO facility_scada (interval, network_id, facility_code, generated, energy, is_forecast, energy_quality_flag)
        SELECT s.interval, s.network_id, :new_facility_code, s.generated, s.energy, s.is_forecast, s.energy_quality_flag
        FROM source s
        ON CONFLICT (interval, network_id, facility_code, is_forecast) DO UPDATE
        SET generated = EXCLUDED.generated,
            energy = EXCLUDED.energy,
            energy_quality_flag = EXCLUDED.energy_quality_flag
        """
    )

    query_generator_delete = text(
        """
        DELETE FROM facility_scada
        WHERE facility_code = :old_facility_code
        AND generated >= 0
        """
    )

    query_aggregate_generator = text(
        """
        WITH source AS (
            SELECT interval, network_id, facility_code, unit_code, fueltech_code, network_region, status_id,
                   generated, energy, emissions, emissions_intensity, market_value
            FROM at_facility_intervals
            WHERE unit_code = :old_facility_code AND generated >= 0
        )
        INSERT INTO at_facility_intervals (
            interval, network_id, facility_code, unit_code, fueltech_code, network_region, status_id,
            generated, energy, emissions, emissions_intensity, market_value
        )
        SELECT s.interval, s.network_id, s.facility_code, :new_facility_code, s.fueltech_code, s.network_region, s.status_id,
               s.generated, s.energy, s.emissions, s.emissions_intensity, s.market_value
        FROM source s
        ON CONFLICT (interval, network_id, facility_code, unit_code) DO UPDATE
        SET generated = EXCLUDED.generated,
            energy = EXCLUDED.energy,
            emissions = EXCLUDED.emissions,
            emissions_intensity = EXCLUDED.emissions_intensity,
            market_value = EXCLUDED.market_value
        """
    )

    query_aggregate_generator_delete = text(
        """
        DELETE FROM at_facility_intervals
        WHERE unit_code = :old_facility_code
        AND generated >= 0
        """
    )

    async with get_write_session() as session:
        for unit in unit_map.values():  # type: ignore  # noqa: B020
            # clear out old records
            if clear_old_records:
                result = await session.execute(
                    text(
                        "delete from facility_scada where facility_code in (:discharge_facility_code, :charge_facility_code) "
                        "and interval >= (select min(interval) from facility_scada where "
                        "facility_code=:bidirectional_facility_code);"
                    ),
                    {
                        "discharge_facility_code": unit.discharge_unit,
                        "charge_facility_code": unit.charge_unit,
                        "bidirectional_facility_code": unit.unit,
                    },
                )

                logger.info(
                    f"Deleted {unit.discharge_unit} and {unit.charge_unit} records newer than {unit.unit}: {result.rowcount}"  # type: ignore
                )

            # Handle charging records
            params = {"new_facility_code": unit.charge_unit, "old_facility_code": unit.unit}
            await session.execute(query_load_template, params)
            await session.execute(query_load_delete, params)
            await session.execute(query_load_aggregate_template, params)
            await session.execute(query_load_aggregate_delete, params)

            logger.info(f"Updated {unit.unit} charge to {unit.charge_unit}")

            # Handle discharging records
            params = {"new_facility_code": unit.discharge_unit, "old_facility_code": unit.unit}
            await session.execute(query_generator, params)
            await session.execute(query_generator_delete, params)
            await session.execute(query_aggregate_generator, params)
            await session.execute(query_aggregate_generator_delete, params)

            logger.info(f"Updated {unit.unit} discharge to {unit.discharge_unit}")

        await session.commit()


async def check_unsplit_batteries() -> list[str]:
    """Check for any battery units in facility_scada that haven't been split into charge/discharge units.

    This method finds battery units that have records in facility_scada within the last 30 days
    but haven't been split into separate charge/discharge units yet.

    Returns:
        list[str]: List of unsplit battery unit codes
    """
    async with get_read_session() as session:
        query = text(
            """
            SELECT DISTINCT fs.facility_code
            FROM facility_scada fs
            INNER JOIN units u ON fs.facility_code = u.code
            WHERE u.fueltech_id = 'battery'
            AND fs.interval >= NOW() - INTERVAL '100 days'
            ORDER BY fs.facility_code
            """
        )

        result = await session.execute(query)
        unsplit_units = [row[0] for row in result]

        if unsplit_units:
            msg = (
                f"[{settings.env.upper()}] Found {len(unsplit_units)} unsplit "
                f"battery units in facility_scada: {', '.join(unsplit_units)}"
            )

            await slack_message(webhook_url=settings.slack_hook_new_facilities, tag_users=settings.slack_admin_alert, message=msg)

            logger.info(msg)

        return unsplit_units


async def run_update_unplit_batteries():
    unplit_battery_units = await check_unsplit_batteries()

    logger.info(f"Found {len(unplit_battery_units)} unsplit battery units")

    for facility_code in unplit_battery_units:
        logger.info(f"Processing {facility_code}")
        await process_battery_history(facility_code=facility_code)


if __name__ == "__main__":
    import asyncio

    unit_map = asyncio.run(run_update_unplit_batteries())

    # for unit in unit_map.values():
    # print(f"{unit.unit} -> {unit.charge_unit} | {unit.discharge_unit}")
