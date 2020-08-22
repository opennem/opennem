"""
    Module to map parameters between versions of opennem
"""


def map_compat_fueltech(fueltech: str) -> str:
    """
        Map old opennem fueltechs to new fueltechs

    """
    if fueltech == "brown_coal":
        return "coal_brown"

    if fueltech == "black_coal":
        return "coal_black"

    if fueltech == "solar":
        return "solar_utility"

    if fueltech == "biomass":
        return "bioenergy_biomass"

    return fueltech


def map_compat_network_region(network_region: str) -> str:
    """
        Map network regions from old to new

        Note that network regions aren't really geos
        and there are networks within geos like DKIS (NT)
        and NWIS (WA) that need to retain their network_region
    """
    if not network_region or not type(network_region) is str:
        return network_region

    network_region = network_region.strip()

    if network_region == "WA1":
        return "WEM"

    return network_region


def map_compat_facility_state(facility_state: str) -> str:
    """
        Maps a current v1 version opennem facility_registry.json state
        to a v3 state

    """
    state = facility_state.lower().strip()

    if state == "commissioned":
        return "operating"

    if state == "decommissioned":
        return "retired"

    return state
