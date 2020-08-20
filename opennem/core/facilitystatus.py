import logging

logger = logging.getLogger(__name__)


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
