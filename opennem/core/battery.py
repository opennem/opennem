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
from opennem.schema.unit import UnitDispatchType

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
    return {
        "COLLIE_ESR1": BatteryUnitMap(unit="COLLIE_ESR1", charge_unit="COLLIE_ESRL1", discharge_unit="COLLIE_ESRG1"),
        "LVES1": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1"),  # latrobe valley
        "ULPBESS1": BatteryUnitMap(unit="ULPBESS1", charge_unit="ULPBESSL1", discharge_unit="ULPBESSG1"),  # ulinda park
        "COLLIE_BESS2": BatteryUnitMap(
            unit="COLLIE_BESS2", charge_unit="COLLIE_BESSL2", discharge_unit="COLLIE_BESSG2"
        ),  # collie
        "SNB01": BatteryUnitMap(unit="SNB01", charge_unit="SNBL01", discharge_unit="SNBG01"),  # supernode
        "TARBESS1": BatteryUnitMap(unit="TARBESS1", charge_unit="TARBESSL1", discharge_unit="TARBESSG1"),  # tarong
        "TEMPB1": BatteryUnitMap(unit="TEMPB1", charge_unit="TEMPBL1", discharge_unit="TEMPBG1"),  # templers
        "WDBESS1": BatteryUnitMap(unit="WDBESS1", charge_unit="WDBESSL1", discharge_unit="WDBESSG1"),  # western downs
        "DALNTH1": BatteryUnitMap(unit="DALNTH1", charge_unit="DALNTHL1", discharge_unit="DALNTHG1"),  # dairymple north
        "DALNTH01": BatteryUnitMap(unit="DALNTH01", charge_unit="DALNTHL1", discharge_unit="DALNTHG1"),  # dairymple north
        "BBATTERY1": BatteryUnitMap(unit="BBATTERY1", charge_unit="BBATTERYL1", discharge_unit="BBATTERYG1"),  # battery
        # station code based?
        "0COLLIE_ESR2": BatteryUnitMap(unit="COLLIE_BESS2", charge_unit="COLLIE_BESSL2", discharge_unit="COLLIE_BESSG2"),
        "0LVBESS": BatteryUnitMap(unit="LVES1", charge_unit="LVESL1", discharge_unit="LVESG1"),  # latrobe valley
        "ULBESS": BatteryUnitMap(unit="ULPBESS1", charge_unit="ULPBESSL1", discharge_unit="ULPBESSG1"),  # ulinda park
        "0SUPERNODE": BatteryUnitMap(unit="SNB01", charge_unit="SNBL01", discharge_unit="SNBG01"),  # supernode
        "0TARONGBESS": BatteryUnitMap(unit="TARBESS1", charge_unit="TARBESSL1", discharge_unit="TARBESSG1"),  # tarong
        "0TEMPLERBESS": BatteryUnitMap(unit="TEMPB1", charge_unit="TEMPBL1", discharge_unit="TEMPBG1"),  # templers
        "WDBESS": BatteryUnitMap(unit="WDBESS1", charge_unit="WDBESSL1", discharge_unit="WDBESSG1"),  # western downs
        "DALNTH": BatteryUnitMap(unit="DALNTH", charge_unit="DALNTHL1", discharge_unit="DALNTHG1"),  # dairymple north
        "BBATTERY": BatteryUnitMap(unit="BBATTERY1", charge_unit="BBATTERYL1", discharge_unit="BBATTERYG1"),  # battery
    }


async def _generate_battery_unit_map() -> dict[str, BatteryUnitMap]:
    """This queries the database for all the bidirectional battery units and returns what each should be mapped to"""

    # if we have a manual map start with that
    unit_map: dict[str, BatteryUnitMap] = _generate_manual_battery_unit_map()

    async with get_read_session() as session:
        facility_query = (
            select(Facility)
            .join(Unit)
            .where(Unit.dispatch_type == UnitDispatchType.BIDIRECTIONAL.value)
            .where(Unit.fueltech_id == "battery")
            .order_by(Facility.code, Unit.code)
        )

        facilities = (await session.execute(facility_query)).scalars().all()

        logger.debug(f"Found {len(facilities)} bidirectional battery facilities")

        for facility in facilities:
            # find the bidirectional unit
            bidirectional_unit = next(
                (
                    unit
                    for unit in facility.units
                    if unit.dispatch_type == UnitDispatchType.BIDIRECTIONAL.value and unit.fueltech_id == "battery"
                ),
                None,
            )

            if not bidirectional_unit:
                logger.warning(f"No bidirectional battery unit found for {facility.code} {facility.name}")
                continue

            if str(bidirectional_unit.code) in unit_map:
                logger.debug(f"Skipping {facility.code} {facility.name} as it has a manual or existing map")
                continue

            # find the charge and discharge units
            charge_unit = list(filter(lambda x: x.fueltech_id == "battery_charging", facility.units))
            discharge_unit = list(filter(lambda x: x.fueltech_id == "battery_discharging", facility.units))

            if not charge_unit:
                logger.info(f"No charge unit found for {facility.code} {facility.name} - needs creation")
                # Add to map anyway for detection purposes, with generated unit codes
                unit_map[str(bidirectional_unit.code)] = BatteryUnitMap(
                    unit=str(bidirectional_unit.code),
                    charge_unit=f"{bidirectional_unit.code}L",  # L for Load
                    discharge_unit=f"{bidirectional_unit.code}G",  # G for Generation
                )
                continue

            if not discharge_unit:
                logger.info(f"No discharge unit found for {facility.code} {facility.name} - needs creation")
                # Still add to map if we have charge unit
                if charge_unit:
                    unit_map[str(bidirectional_unit.code)] = BatteryUnitMap(
                        unit=str(bidirectional_unit.code),
                        charge_unit=charge_unit[0].code,
                        discharge_unit=f"{bidirectional_unit.code}G",  # G for Generation
                    )
                continue

            if len(charge_unit) > 1:
                logger.warning(f"Multiple charge units found for {facility.code} {facility.name}")
                continue

            if len(discharge_unit) > 1:
                logger.warning(f"Multiple discharge units found for {facility.code} {facility.name}")
                continue

            # Validate fueltechs
            if charge_unit[0].fueltech_id != "battery_charging":
                logger.error(
                    f"Charge unit {charge_unit[0].code} for {facility.code} has incorrect fueltech: {charge_unit[0].fueltech_id}"
                )
                continue

            if discharge_unit[0].fueltech_id != "battery_discharging":
                logger.error(
                    f"Discharge unit {discharge_unit[0].code} for {facility.code} "
                    f"has incorrect fueltech: {discharge_unit[0].fueltech_id}"
                )
                continue

            unit_map[str(bidirectional_unit.code)] = BatteryUnitMap(
                unit=str(bidirectional_unit.code),
                charge_unit=str(charge_unit[0].code),
                discharge_unit=str(discharge_unit[0].code),
            )

            # create the charge and discharge units

    return unit_map


async def process_battery_history(facility_code: str | None = None, clear_old_records: bool = False):
    """This processes the history of facility_scada and creates split battery records.

    NEW BEHAVIOR: Original bidirectional records are preserved. This function only creates
    the missing charge/discharge records alongside the existing bidirectional records.
    """
    unit_map = await get_battery_unit_map()

    if facility_code and facility_code not in unit_map:
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

    async with get_write_session() as session:
        try:
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

                # Handle charging records (create charge records for negative generation)
                params = {"new_facility_code": unit.charge_unit, "old_facility_code": unit.unit}
                await session.execute(query_load_template, params)

                logger.info(f"Created {unit.charge_unit} records for {unit.unit} charging intervals")

                # Handle discharging records (create discharge records for positive generation)
                params = {"new_facility_code": unit.discharge_unit, "old_facility_code": unit.unit}
                await session.execute(query_generator, params)

                logger.info(f"Created {unit.discharge_unit} records for {unit.unit} discharging intervals")

            await session.commit()
        except Exception as e:
            logger.error(f"Error processing battery history: {e}")
            await session.rollback()
            raise


UNSPLIT_CHECK_WINDOW = "24 hours"
UNSPLIT_TOLERANCE_ROWS = 2  # boundary drift between bidirectional and split crawl batches


async def check_unsplit_batteries() -> list[str]:
    """Flag bidirectional batteries whose split rows lag their bidirectional activity.

    Per battery, in the same window, compare:
      neg_rows (bidirectional intervals with generated < 0)  vs  charge_unit rows
      pos_rows (bidirectional intervals with generated >= 0) vs  discharge_unit rows

    Only flag when one side has bidirectional activity but the corresponding split
    side has materially fewer rows. A battery that only charged (or only discharged)
    in the window is NOT flagged — its zero-row split side is correct.

    Returns:
        list[str]: bidirectional unit codes whose splits are lagging
    """
    battery_unit_map = await get_battery_unit_map()

    # Dedupe alias triples in the manual map so we don't double-flag the same physical battery
    seen: set[tuple[str, str]] = set()
    triples: list[tuple[str, str, str]] = []
    for bmap in battery_unit_map.values():
        key = (str(bmap.charge_unit), str(bmap.discharge_unit))
        if key in seen:
            continue
        seen.add(key)
        triples.append((str(bmap.unit), str(bmap.charge_unit), str(bmap.discharge_unit)))

    logger.info(f"Checking {len(triples)} battery triples for split lag (window: {UNSPLIT_CHECK_WINDOW})")

    bi_codes = [t[0] for t in triples]
    chg_codes = [t[1] for t in triples]
    dis_codes = [t[2] for t in triples]

    bi_query = text(
        f"""
        SELECT
            facility_code,
            COUNT(*) FILTER (WHERE generated <  0) AS neg_rows,
            COUNT(*) FILTER (WHERE generated >= 0) AS pos_rows
        FROM facility_scada
        WHERE facility_code = ANY(:codes)
          AND interval >= NOW() - INTERVAL '{UNSPLIT_CHECK_WINDOW}'
          AND is_forecast = FALSE
        GROUP BY facility_code
        """
    )
    split_query = text(
        f"""
        SELECT facility_code, COUNT(*) AS rows
        FROM facility_scada
        WHERE facility_code = ANY(:codes)
          AND interval >= NOW() - INTERVAL '{UNSPLIT_CHECK_WINDOW}'
          AND is_forecast = FALSE
        GROUP BY facility_code
        """
    )

    async with get_read_session() as session:
        bi_res = (await session.execute(bi_query, {"codes": bi_codes})).fetchall()
        chg_res = (await session.execute(split_query, {"codes": chg_codes})).fetchall()
        dis_res = (await session.execute(split_query, {"codes": dis_codes})).fetchall()

    bi_counts: dict[str, tuple[int, int]] = {r[0]: (int(r[1]), int(r[2])) for r in bi_res}
    chg_counts: dict[str, int] = {r[0]: int(r[1]) for r in chg_res}
    dis_counts: dict[str, int] = {r[0]: int(r[1]) for r in dis_res}

    unsplit_units: list[str] = []
    tol = UNSPLIT_TOLERANCE_ROWS
    for bi, chg, dis in triples:
        bi_neg, bi_pos = bi_counts.get(bi, (0, 0))
        if bi_neg == 0 and bi_pos == 0:
            continue  # bidirectional had no activity in window — nothing to split
        chg_rows = chg_counts.get(chg, 0)
        dis_rows = dis_counts.get(dis, 0)
        chg_lag = bi_neg > 0 and (bi_neg - chg_rows) > tol
        dis_lag = bi_pos > 0 and (bi_pos - dis_rows) > tol
        if chg_lag or dis_lag:
            logger.info(
                f"Battery {bi} split lag: bi_neg={bi_neg} vs chg={chg_rows} ({chg}), bi_pos={bi_pos} vs dis={dis_rows} ({dis})"
            )
            unsplit_units.append(bi)

    if unsplit_units:
        msg = (
            f"[{settings.env.upper()}] Found {len(unsplit_units)} battery units with missing "
            f"split records: {', '.join(unsplit_units)}"
        )
        await slack_message(webhook_url=settings.slack_hook_new_facilities, tag_users=settings.slack_admin_alert, message=msg)
        logger.info(msg)
    else:
        logger.info("No batteries with split lag")

    return unsplit_units


async def run_update_unsplit_batteries():
    unsplit_battery_units = await check_unsplit_batteries()

    logger.info(f"Found {len(unsplit_battery_units)} unsplit battery units")

    for facility_code in unsplit_battery_units:
        logger.info(f"Processing {facility_code}")
        await process_battery_history(facility_code=facility_code)


if __name__ == "__main__":
    import asyncio

    # unit_map = asyncio.run(run_update_unsplit_batteries())

    async def test():
        await process_battery_history(facility_code="LVES1")

    asyncio.run(run_update_unsplit_batteries())

    # for unit in unit_map.values():
    # print(f"{unit.unit} -> {unit.charge_unit} | {unit.discharge_unit}")
