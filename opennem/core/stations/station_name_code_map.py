from typing import Optional

from opennem.core.loader import load_data

STATION_NAME_CODE_MAP = load_data("station_name_code_map.json")


def station_name_code_map(station_name: str) -> Optional[str]:
    if station_name.strip() in STATION_NAME_CODE_MAP:
        return STATION_NAME_CODE_MAP[station_name]
    return None
