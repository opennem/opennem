from opennem.core.normalizers import normalize_duid
from opennem.core.unit_parser import UnitSchema


def get_unit_code(
    duid: str, unit: UnitSchema, station_name: str = None
) -> str:
    """
        This takes the duid from the network and the unit info and creates a unique
        opennem code

        This should be unique across all units for a network
    """

    duid_clean = normalize_duid(duid)
    unit_id = None
    # @TODO - check if we can strip, probably not a good idea

    if not duid:

        if not station_name:
            raise Exception(
                "Cannot generate a unit code without both duid and station name"
            )

        duid = get_basecode(station_name)

    if not duid_clean.endswith(str(unit.id)):
        unit_id = str(unit.id)

    components = [duid_clean, unit.alias, unit_id]

    # empty out None's
    components = [i for i in components if i]

    unit_code = "_".join(components)

    return unit_code


OPENNEM_CODE_PREFIX = "0N"


def get_basecode(station_name: str) -> str:
    """
        Generate a code from the station name when there isn't an DUID

        We prefix these with 0N
    """

    if not type(station_name) is str or not station_name:
        raise Exception("Expected to generate a code with no station name")

    comps = station_name.strip().split(" ")

    comps = [i[0] for i in comps]

    comps.insert(0, OPENNEM_CODE_PREFIX)

    basecode = "".join(comps).upper()

    return basecode


def duid_is_ocode(duid: str) -> bool:
    return duid.startswith(OPENNEM_CODE_PREFIX)
