from typing import List

import pint

from opennem.core.loader import load_data
from opennem.schema.units import UnitDefinition

unit_registry = pint.UnitRegistry()
Q = unit_registry.Quantity


def load_units() -> List[UnitDefinition]:
    units_dics = load_data("units.json")

    units = [UnitDefinition(**i) for i in units_dics]

    # unique aliases in set
    assert len([i.name_alias for i in units if i.name_alias]) == len(
        set([i.name_alias for i in units if i.name_alias])
    ), "Unique names for aliases required"

    # unique names in
    assert len([i.name for i in units]) == len(
        set([i.name for i in units])
    ), "Unique unit names required"

    return units


UNITS = load_units()

UNITS_SUPPORTED = [i.unit for i in UNITS]

UNIT_TYPES_SUPPORTED = set([i.unit_type for i in UNITS])


def get_unit(unit_human: str) -> UnitDefinition:
    global UNITS

    # Lazy load
    if not UNITS:
        UNITS = load_units()

    unit_lookup = list(
        filter(
            lambda x: x.name_alias == unit_human or x.name == unit_human, UNITS
        )
    )

    if unit_lookup:
        return unit_lookup.pop()

    raise Exception("Invalid interval {} not mapped".format(unit_human))
