import logging

from opennem.core.loader import load_data

logger = logging.getLogger(__name__)


def load_statuses() -> dict:
    statuses = load_data("facility_status.json", from_fixture=True)

    status_dict = {}

    for s in statuses:
        _code = s.get("code", None)
        status_dict[_code] = s

    return status_dict


FACILITY_STATUS_FIXTURE = load_statuses()


def map_aemo_facility_status(facility_status: str) -> str:
    """
        Maps an AEMO facility status to an Opennem facility status


    """

    unit_status = facility_status.lower().strip()

    if unit_status.startswith("in service"):
        return "operating"

    if unit_status.startswith("in commissioning"):
        return "commissioning"

    if unit_status.startswith("committed"):
        return "committed"

    if unit_status.startswith("maturing"):
        return "maturing"

    if unit_status.startswith("emerging"):
        return "emerging"

    raise Exception(
        "Could not find AEMO status for facility status: {}".format(
            unit_status
        )
    )


def parse_facility_status(status_code: str) -> dict:
    if status_code not in FACILITY_STATUS_FIXTURE.keys():
        raise Exception("Invalid facility status: {}".format(status_code))

    return FACILITY_STATUS_FIXTURE[status_code]
