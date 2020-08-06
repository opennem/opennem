"""
    Parse facility codes facility ids

"""

WEM_CODE_SUFFIXES = ["plant"]


def parse_wem_facility_code(facility_code: str) -> str:
    """
        Parses WEM facility codes into station_code and facility_code

        If the suffix is in the map include it

        ex. PINJAR_GT7 becomes PINJAR and PINJAR_GT7
    """

    if not type(facility_code) is str:
        raise Exception("Invalid facilty code: {}".format(facility_code))

    if not facility_code:
        # Exception?
        return None

    if "_" not in facility_code:
        return facility_code

    comp = facility_comp = facility_code.split("_")

    num_comp = len(comp)

    if comp[num_comp - 1].lower() not in WEM_CODE_SUFFIXES:
        facility_comp = comp[: num_comp - 1]

    return "_".join(facility_comp)
