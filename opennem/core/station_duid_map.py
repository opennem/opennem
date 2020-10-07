from typing import Optional

from opennem.core.loader import load_data

STATION_CODE_REMAP = {"SWAN_B": "SWANBANK", "SWAN_E": "SWANBANK_E"}


def map_old_station_names(station_code: str) -> str:
    if station_code in STATION_CODE_REMAP:
        return STATION_CODE_REMAP[station_code]

    return station_code


STATION_DUID_MAP = load_data("facility_duid_map.json")


def facility_map_station(
    duid: str, default_station: Optional[str] = None
) -> Optional[str]:
    """
        Maps duid -> station code

    """

    if not type(STATION_DUID_MAP) is dict:
        raise Exception("Station duid map invalid data type")

    if duid in STATION_DUID_MAP:
        return STATION_DUID_MAP[duid]

    if default_station:
        station_code = map_old_station_names(default_station)

    return station_code


def facility_has_station_remap(duid: str) -> bool:
    return duid in STATION_DUID_MAP
