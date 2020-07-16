import logging

logger = logging.getLogger(__name__)


def lookup_facility_status(unit_status):

    unit_status = unit_status or ""

    unit_status = unit_status.lower().strip()

    if unit_status.startswith("in service"):
        return "operating"

    if unit_status.startswith("in commissioning"):
        return "commissioning"

    if unit_status.startswith("committed"):
        return "committed"

    if unit_status.startswith("maturing"):
        return "maturing"

    if unit_status.startswith("Emerging"):
        return "emerging"

    logger.error(
        "Could not find status for unit status: {}".format(unit_status)
    )

    return None
