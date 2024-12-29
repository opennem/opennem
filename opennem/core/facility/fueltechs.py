from opennem.core.loader import load_data


def load_fueltechs() -> dict:
    fueltechs = load_data("fueltechs.json", from_fixture=True)

    fueltechs_dict = {}

    for s in fueltechs:
        _code = s.get("code", None)
        fueltechs_dict[_code] = s

    return fueltechs_dict


FACILITY_FUELTECH_FIXTURE = load_fueltechs()
