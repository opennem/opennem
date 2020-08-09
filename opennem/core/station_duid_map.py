from typing import Optional

from opennem.core import load_data_json

STATION_DUID_MAP = load_data_json("facility_duid_map.json")


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

    return default_station


def facility_has_station_remap(duid: str) -> bool:
    return duid in STATION_DUID_MAP
