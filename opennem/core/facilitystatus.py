import logging

logger = logging.getLogger(__name__)


def map_v3_states(state):
    """
        Maps a current v1 version opennem facility_registry.json state
        to a v3 state

    """
    state = state.lower().strip()

    if state == "commissioned":
        return "operating"

    if state == "decommissioned":
        return "retired"

    return state


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
