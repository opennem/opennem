import re
from typing import Optional

from opennem.core.normalizers import normalize_duid
from opennem.core.unit_parser import UnitSchema


def get_unit_code(
    unit: UnitSchema,
    duid: Optional[str] = None,
    station_name: Optional[str] = None,
) -> str:
    """
        This takes the duid from the network and the unit info and creates a unique
        opennem code

        This should be unique across all units for a network
    """

    unit_id = None
    # @TODO - check if we can strip, probably not a good idea

    if not duid:

        if not station_name:
            raise Exception(
                "Cannot generate a unit code without both duid and station name"
            )

        duid = get_basecode(station_name)

    duid_clean = normalize_duid(duid)

    if not duid_clean.endswith(str(unit.id)):
        unit_id = str(unit.id)

    if unit_id == 1:
        unit_id = None

    components = [duid_clean, unit.alias, unit_id]

    # empty out None's
    components = [i for i in components if i]

    unit_code = "_".join(components)

    return unit_code


OPENNEM_CODE_PREFIX = "0N"


__alphanum_strip = re.compile(r"[\W_\ ]+")


def clean_name_for_basecode(station_name: str) -> str:
    """
        Cleans up the name in prep to generate a basecode
    """

    return __alphanum_strip.sub(" ", station_name.strip())


def get_basecode(station_name: str) -> str:
    """
        Generate a code from the station name when there isn't an DUID

        We prefix these with 0N
    """

    if not type(station_name) is str or not station_name:
        raise Exception("Expected to generate a code with no station name")

    MIN_DUID_LENGTH = 4
    MAX_DUID_LENGTH = 6

    station_name = clean_name_for_basecode(station_name)

    comps = station_name.split(" ")

    num_words = len(comps)

    if num_words > MAX_DUID_LENGTH:
        comps = comps[:MAX_DUID_LENGTH]

    if num_words > MIN_DUID_LENGTH:
        num_words = MIN_DUID_LENGTH

    comps = [i[0 : MIN_DUID_LENGTH + 1 - num_words] for i in comps]

    comps.insert(0, OPENNEM_CODE_PREFIX)

    basecode = "".join(comps).upper()

    return basecode


def duid_is_ocode(duid: str) -> bool:
    return duid.startswith(OPENNEM_CODE_PREFIX)
