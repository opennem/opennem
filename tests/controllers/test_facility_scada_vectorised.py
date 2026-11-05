"""The vectorised build_facility_scada_records must emit exactly what the old row-wise apply did.

legacy_build is a frozen copy of generate_facility_scada before the battery/alias steps were
vectorised (it held the event loop for seconds on a next-day dispatch file).
"""

import random
from collections.abc import Hashable
from typing import Any

import pandas as pd
import pytest

from opennem.controllers.nem import FACILITY_SCADA_COLUMN_NAMES, build_facility_scada_records
from opennem.core.battery import HISTORIC_UNIT_ALIASES, BatteryUnitMap, _generate_manual_battery_unit_map
from opennem.core.networks import NetworkNEM
from opennem.schema.network import NetworkAEMORooftop, NetworkSchema


def legacy_build(
    records: list[dict[str, Any]],
    battery_unit_map: dict[str, BatteryUnitMap],
    network: NetworkSchema = NetworkNEM,
    interval_field: str = "settlementdate",
    facility_code_field: str = "duid",
    power_field: str = "scadavalue",
    energy_field: str | None = None,
    energy_storage_field: str | None = None,
    is_forecast: bool = False,
) -> list[dict[Hashable, Any]]:
    df = pd.DataFrame().from_records(records)
    column_renames = {interval_field: "interval", power_field: "generated", facility_code_field: "facility_code"}
    if energy_field:
        column_renames[energy_field] = "energy"
    else:
        df["energy"] = None
    if energy_storage_field:
        column_renames[energy_storage_field] = "energy_storage"
    else:
        df["energy_storage"] = None
    df = df.rename(columns=column_renames)
    df["network_id"] = network.code
    df["is_forecast"] = is_forecast
    df["eoi_quantity"] = None
    df["energy_quality_flag"] = 0
    df.interval = pd.to_datetime(df.interval)
    df.generated = pd.to_numeric(df.generated)
    df["generated"] = df["generated"].fillna(0)
    df = df[FACILITY_SCADA_COLUMN_NAMES]

    def is_battery_unit(row) -> bool:
        return row["facility_code"] in battery_unit_map

    battery_mask = df.apply(is_battery_unit, axis=1)
    battery_copies = df.loc[battery_mask].copy()
    battery_copies["battery_copy"] = True
    df["battery_copy"] = False
    if len(battery_copies) > 0:
        df = pd.concat([df, battery_copies], ignore_index=True)

    def map_battery_code(row):
        facility_code = row["facility_code"]
        generated = row["generated"]
        if facility_code in battery_unit_map:
            battery_map = battery_unit_map[facility_code]
            if generated < 0:
                return battery_map.charge_unit
            else:
                return battery_map.discharge_unit
        return facility_code

    def map_battery_generation(row):
        facility_code = row["facility_code"]
        generated = row["generated"]
        for _, battery_map in battery_unit_map.items():
            if facility_code == battery_map.charge_unit:
                return abs(generated)
        return generated

    battery_copy_mask = df["battery_copy"]
    df.loc[battery_copy_mask, "facility_code"] = df.loc[battery_copy_mask].apply(map_battery_code, axis=1)
    df.loc[battery_copy_mask, "generated"] = df.loc[battery_copy_mask].apply(map_battery_generation, axis=1)
    df = df.drop(columns=["battery_copy"])

    def is_alias_unit(row) -> bool:
        return row["facility_code"] in HISTORIC_UNIT_ALIASES

    def map_alias_code(row) -> str:
        return HISTORIC_UNIT_ALIASES[row["facility_code"]]

    alias_copies = df.loc[df.apply(is_alias_unit, axis=1)].copy()
    if len(alias_copies) > 0:
        alias_copies["facility_code"] = alias_copies.apply(map_alias_code, axis=1)
        df = pd.concat([df, alias_copies], ignore_index=True)

    df["energy"] = df.generated / (60 / network.interval_size)
    df.set_index(["interval", "network_id", "facility_code", "is_forecast"], inplace=True)
    df_deduped = df[~df.index.duplicated(keep="last")]
    df_reset = df_deduped.reset_index(inplace=False)
    return df_reset[FACILITY_SCADA_COLUMN_NAMES].to_dict("records")


BATTERY_MAP = _generate_manual_battery_unit_map()

# a map whose discharge unit is another map's charge unit, the generation rule keys off any charge unit
EXOTIC_MAP = {
    **BATTERY_MAP,
    "XBAT1": BatteryUnitMap(unit="XBAT1", charge_unit="XBATL1", discharge_unit="LVESL1"),
}

NORMAL_CODES = ["BAYSW1", "ER01", "MACARTH1", "SNOWYGJP", "KEPBL1", "0NORMAL"]


def _value(rng: random.Random) -> Any:
    choice = rng.random()
    if choice < 0.05:
        return None
    if choice < 0.15:
        return "0"
    if choice < 0.2:
        return "-0.0"
    return f"{rng.uniform(-300, 300):.5f}"


def _records(rng: random.Random, codes: list[str], n: int, storage: bool = False) -> list[dict[str, Any]]:
    out = []
    for _ in range(n):
        minute = rng.randrange(0, 24 * 12) * 5
        record = {
            "settlementdate": f"2026/11/0{rng.randint(1, 3)} {minute // 60:02d}:{minute % 60:02d}:00",
            "duid": rng.choice(codes),
            "scadavalue": _value(rng),
        }
        if storage:
            record["energy_storage"] = rng.choice([None, "12.5", "0"])
        out.append(record)
    return out


ALL_CODES = NORMAL_CODES + list(BATTERY_MAP) + list(HISTORIC_UNIT_ALIASES) + ["XBAT1", "LVESL1", "BBATTERYG1"]


@pytest.mark.parametrize("seed", range(12))
@pytest.mark.parametrize("unit_map", [BATTERY_MAP, EXOTIC_MAP, {}], ids=["manual", "exotic", "empty"])
def test_vectorised_matches_legacy(seed: int, unit_map: dict[str, BatteryUnitMap]) -> None:
    rng = random.Random(seed)
    records = _records(rng, ALL_CODES, n=rng.choice([1, 7, 400]))

    expected = legacy_build(records, unit_map)
    got = build_facility_scada_records(records, unit_map)

    pd.testing.assert_frame_equal(pd.DataFrame(got), pd.DataFrame(expected))
    assert got == expected


@pytest.mark.parametrize("seed", range(4))
def test_vectorised_matches_legacy_unit_solution(seed: int) -> None:
    """dispatch_unit_solution shape: initialmw power plus an energy_storage column"""
    rng = random.Random(seed)
    records = _records(rng, ALL_CODES, n=300, storage=True)
    for r in records:
        r["initialmw"] = r.pop("scadavalue")

    kwargs: dict[str, Any] = {"power_field": "initialmw", "energy_storage_field": "energy_storage"}
    expected = legacy_build(records, BATTERY_MAP, **kwargs)
    got = build_facility_scada_records(records, BATTERY_MAP, **kwargs)

    pd.testing.assert_frame_equal(pd.DataFrame(got), pd.DataFrame(expected))
    assert got == expected


def test_vectorised_matches_legacy_rooftop_forecast() -> None:
    """rooftop shape: no battery or alias codes, 30 minute network, forecast flag"""
    rng = random.Random(99)
    records = [
        {"interval_datetime": f"2026/11/01 {h:02d}:{m:02d}:00", "regionid": region, "powermean": _value(rng)}
        for h in range(24)
        for m in (0, 30)
        for region in ("NSW1", "QLD1", "VIC1", "SA1", "TAS1")
    ]
    kwargs: dict[str, Any] = {
        "network": NetworkAEMORooftop,
        "interval_field": "interval_datetime",
        "facility_code_field": "regionid",
        "power_field": "powermean",
        "is_forecast": True,
    }
    expected = legacy_build(records, BATTERY_MAP, **kwargs)
    got = build_facility_scada_records(records, BATTERY_MAP, **kwargs)

    pd.testing.assert_frame_equal(pd.DataFrame(got), pd.DataFrame(expected))
    assert got == expected


def test_battery_copy_codes_and_sign() -> None:
    records = [
        {"settlementdate": "2026/11/01 00:05:00", "duid": "LVES1", "scadavalue": "-40"},
        {"settlementdate": "2026/11/01 00:10:00", "duid": "LVES1", "scadavalue": "30"},
        {"settlementdate": "2026/11/01 00:05:00", "duid": "BBATTERY", "scadavalue": "-1"},
    ]
    got = {(r["facility_code"], r["interval"].minute): r["generated"] for r in build_facility_scada_records(records, BATTERY_MAP)}

    assert got[("LVES1", 5)] == -40
    assert got[("LVESL1", 5)] == 40
    assert got[("LVES1", 10)] == 30
    assert got[("LVESG1", 10)] == 30
    # alias: copied 1:1, never sign-split
    assert got[("BBATTERY", 5)] == -1
    assert got[("BBATTERYG1", 5)] == -1
