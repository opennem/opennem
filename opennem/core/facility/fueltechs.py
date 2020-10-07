from typing import Optional

from opennem.core.loader import load_data


def load_fueltechs() -> dict:
    fueltechs = load_data("fueltechs.json", from_fixture=True)

    fueltechs_dict = {}

    for s in fueltechs:
        _code = s.get("code", None)
        fueltechs_dict[_code] = s

    return fueltechs_dict


FACILITY_FUELTECH_FIXTURE = load_fueltechs()


def parse_facility_fueltech(fueltech_code: Optional[str]) -> Optional[dict]:
    if fueltech_code is None:
        return None

    if fueltech_code not in FACILITY_FUELTECH_FIXTURE.keys():
        raise Exception("Invalid facility fueltech: {}".format(fueltech_code))

    return FACILITY_FUELTECH_FIXTURE[fueltech_code]
