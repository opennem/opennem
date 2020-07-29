from opennem.core.normalizers import normalize_duid
from opennem.core.unit_parser import UnitSchema


def get_unit_code(duid: str, unit: UnitSchema) -> str:
    """
        This takes the duid from the network and the unit info and creates a unique
        opennem code

        This should be unique across all units for a network
    """

    duid_clean = normalize_duid(duid)
    unit_id = None
    # @TODO - check if we can strip, probably not a good idea

    if not duid_clean.endswith(str(unit.id)):
        unit_id = str(unit.id)

    components = [duid_clean, unit.alias, unit_id]

    # empty out None's
    components = [i for i in components if i]

    unit_code = "_".join(components)

    return unit_code
