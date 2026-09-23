"""
Blank AEMO rooftop measurements must be dropped, not stored as 0 MW (#660).

AEMO publishes an empty POWER with QI=0 in ROOFTOP_PV_ACTUAL when it has no measurement for a
region and interval. Those rows have to leave the interval missing so it is interpolated.
"""

from unittest.mock import AsyncMock, patch

import pytest

from opennem.controllers.nem import process_rooftop_actual
from opennem.core.parsers.aemo.mms import AEMOTableSchema


def _rooftop_table(records: list[dict]) -> AEMOTableSchema:
    fields = ["interval_datetime", "regionid", "power", "qi", "type", "lastchanged"]
    return AEMOTableSchema(
        name="actual",
        namespace="rooftop",
        fields=fields,
        fieldnames=fields,
        records=records,
    )


def _record(interval: str, region: str, power: str, qi: str) -> dict:
    return {
        "interval_datetime": interval,
        "regionid": region,
        "power": power,
        "qi": qi,
        "type": "MEASUREMENT",
        "lastchanged": interval,
    }


async def _run(records: list[dict]) -> tuple[list[dict], AsyncMock]:
    bulk_insert = AsyncMock(side_effect=lambda _table, rows, _fields: len(rows))

    with (
        patch("opennem.controllers.nem.get_battery_unit_map", new=AsyncMock(return_value={})),
        patch("opennem.controllers.nem.bulkinsert_mms_items", new=bulk_insert),
    ):
        await process_rooftop_actual(_rooftop_table(records))

    stored = bulk_insert.call_args.args[1] if bulk_insert.call_args else []
    return stored, bulk_insert


@pytest.mark.asyncio
async def test_blank_measurement_dropped_valid_kept() -> None:
    # the SA1 sequence from the 2024-12 MMSDM archive quoted in #660
    records = [
        _record("2024/12/10 10:00:00", "SA1", "1473.396", "0.7"),
        _record("2024/12/10 10:30:00", "SA1", "", "0"),
        _record("2024/12/10 11:00:00", "SA1", "", "0"),
        _record("2024/12/10 11:30:00", "SA1", "1783.243", "1"),
    ]

    stored, _ = await _run(records)

    by_interval = {r["interval"].strftime("%H:%M"): r["generated"] for r in stored}

    assert by_interval == {"10:00": pytest.approx(1473.396), "11:30": pytest.approx(1783.243)}
    assert all(r["facility_code"] == "ROOFTOP_NEM_SA" for r in stored)


@pytest.mark.asyncio
async def test_none_and_whitespace_power_dropped() -> None:
    records = [
        _record("2024/12/10 10:30:00", "NSW1", "  ", "0"),
        {**_record("2024/12/10 10:30:00", "VIC1", "", "0"), "power": None},
        _record("2024/12/10 10:30:00", "QLD1", "2500.5", "1"),
    ]

    stored, _ = await _run(records)

    assert [(r["facility_code"], r["generated"]) for r in stored] == [("ROOFTOP_NEM_QLD", pytest.approx(2500.5))]


@pytest.mark.asyncio
async def test_real_zero_measurement_kept() -> None:
    # a measured 0 overnight is a real value, only blanks are missing
    stored, _ = await _run([_record("2024/12/10 02:00:00", "TAS1", "0", "1")])

    assert len(stored) == 1
    assert stored[0]["generated"] == 0


@pytest.mark.asyncio
async def test_all_blank_skips_insert() -> None:
    stored, bulk_insert = await _run([_record("2024/09/05 14:00:00", "SA1", "", "0")])

    assert stored == []
    bulk_insert.assert_not_called()
