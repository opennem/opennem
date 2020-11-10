"""
    Map network regions to BOM stations
"""

from typing import Optional

from opennem.core.loader import load_data

NETWORK_REGION_BOM_STATION = load_data("network_region_bom_station_map.json")


def get_network_region_weather_station(region_code: str) -> Optional[str]:
    """
        Maps a network region to a weather station id

    """
    if not type(NETWORK_REGION_BOM_STATION) is dict:
        raise Exception("NETWORK_REGION_BOM_STATION invalid data type")

    if region_code in NETWORK_REGION_BOM_STATION:
        return NETWORK_REGION_BOM_STATION[region_code]

    return None
