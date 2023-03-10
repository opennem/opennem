from opennem.core.loader import load_data


def load_fueltechs() -> dict:
    fueltechs = load_data("fueltechs.json", from_fixture=True)

    fueltechs_dict = {}

    for s in fueltechs:
        _code = s.get("code", None)
        fueltechs_dict[_code] = s

    return fueltechs_dict


FACILITY_FUELTECH_FIXTURE = load_fueltechs()


def parse_facility_fueltech(fueltech_code: str | None) -> dict | None:
    if fueltech_code is None:
        return None

    if fueltech_code not in FACILITY_FUELTECH_FIXTURE.keys():
        raise Exception(f"Invalid facility fueltech: {fueltech_code}")

    return FACILITY_FUELTECH_FIXTURE[fueltech_code]
