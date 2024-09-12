""" "
Methods for fueltech groups
"""

from opennem.core.loader import load_data
from opennem.schema.fueltech_group import FueltechGroupSchema


class FueltechGroupException(Exception): ...


def _load_fueltech_groups() -> list[FueltechGroupSchema]:
    fixture = load_data("fueltech_groups.json", from_fixture=True)

    fueltechs = []

    for f in fixture:
        fueltech_group_model = FueltechGroupSchema(**f)
        fueltechs.append(fueltech_group_model)

    return fueltechs


_FUELTECH_GROUPS: list[FueltechGroupSchema] = _load_fueltech_groups()


def get_fueltech_group(code: str) -> FueltechGroupSchema:
    _code = code.strip().lower()

    if _lookup := list(filter(lambda x: x.code == _code, _FUELTECH_GROUPS)):
        return _lookup.pop()
    else:
        raise FueltechGroupException(f"Fueltech {_code} not found")


def get_fueltech_groups() -> list[FueltechGroupSchema]:
    return _FUELTECH_GROUPS


ALL_FUELTECH_GROUP_CODES = [i.code for i in _FUELTECH_GROUPS]

if __name__ == "__main__":
    fueltech = get_fueltech_group("coal")
    print(fueltech)
