from opennem.core.loader import load_data

SINGLE_UNITS = load_data("single_units.json")


def facility_unit_numbers_are_single(facility_duid: str) -> bool:
    """
        These units have unit numbers that are single units rather than ranges.

        ex. GT 1-2 means unit of alias GT1 and id 2 rather than alias GT and range 1-2

    """

    if not type(SINGLE_UNITS) is list:
        raise Exception("Error loading facility station map: not a list")

    return facility_duid in SINGLE_UNITS
