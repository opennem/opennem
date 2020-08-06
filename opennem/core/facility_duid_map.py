from opennem.core import load_data_json

FACILITY_DUID_MAP = load_data_json("facility_duid_map.json")


def facility_duid_map(duid: str) -> str:
    """


    """
    if not type(FACILITY_DUID_MAP) is dict:
        raise Exception("Facility duid map invalid data type")

    if duid in FACILITY_DUID_MAP:
        return FACILITY_DUID_MAP[duid]

    return duid


def duid_is_retired(duid: str) -> bool:
    return duid in FACILITY_DUID_MAP
