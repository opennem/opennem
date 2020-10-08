from opennem.core.loader import load_data

FACILITY_DUID_MAP = load_data("facility_duid_map.json")


def facility_duid_map(duid: str) -> str:
    """
        Maps a DUID to a Facility code

    """
    if not type(FACILITY_DUID_MAP) is dict:
        raise Exception("Facility duid map invalid data type")

    if duid in FACILITY_DUID_MAP:
        return FACILITY_DUID_MAP[duid]

    return duid


def duid_is_retired(duid: str) -> bool:
    return duid in FACILITY_DUID_MAP
