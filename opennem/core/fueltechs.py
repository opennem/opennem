import logging

from opennem.core.loader import load_data
from opennem.schema.fueltech import FueltechSchema

logger = logging.getLogger(__name__)


def get_fueltechs() -> list[FueltechSchema]:
    fixture = load_data("fueltechs.json", from_fixture=True)

    fueltechs = []

    for f in fixture:
        _f = FueltechSchema(**f)
        fueltechs.append(_f)

    return fueltechs


_FUELTECHS: list[FueltechSchema] = get_fueltechs()


def get_fueltech(code: str) -> FueltechSchema:
    _code = code.strip().lower()

    if _lookup := list(filter(lambda x: x.code == _code, _FUELTECHS)):
        return _lookup.pop()
    else:
        raise ValueError(f"Fueltech {_code} not found")


ALL_FUELTECH_CODES = [i.code for i in get_fueltechs()]
