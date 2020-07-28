import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "data")


def load_single_units(fixture_name):
    fixture_path = os.path.join(DATA_PATH, fixture_name)

    if not os.path.isfile(fixture_path):
        raise Exception("Not a file: {}".format(fixture_path))

    fixture = None

    with open(fixture_path) as fh:
        fixture = json.load(fh)

    return fixture


SINGLE_UNITS = load_single_units("single_units.json")


def facility_unit_numbers_are_single(facility_duid):
    """
        These units have unit numbers that are single units rather than ranges.

        ex. GT 1-2 means unit of alias GT1 and id 2 rather than alias GT and range 1-2

    """
    if not type(SINGLE_UNITS) is list:
        raise Exception("Error loading facility station map: not a list")

    return facility_duid in SINGLE_UNITS
