from opennem.core.loader import load_data

STATION_NAME_MAP = load_data("station_name_maps.json")


def station_map_name(station_name):
    """
        Clean names manually using a map

    """
    if type(station_name) is not str:
        return station_name

    if not type(STATION_NAME_MAP) is dict:
        raise Exception("Error loading station name maps: not a dict")

    if station_name in STATION_NAME_MAP:
        return STATION_NAME_MAP[station_name]

    for map_name in STATION_NAME_MAP.keys():
        if station_name.lower().startswith(map_name.lower()):
            return STATION_NAME_MAP[map_name]

    return station_name
