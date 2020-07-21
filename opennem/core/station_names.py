import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


def load_facility_stations(fixture_name):
    fixture_path = os.path.join(DATA_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture


STATION_NAME_MAP = load_facility_stations("station_name_maps.json")


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
