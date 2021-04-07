from typing import List

from opennem.core.normalizers import normalize_duid


def duid_in_case(facility_codes: List[str]) -> str:
    return ",".join(["'{}'".format(i) for i in map(normalize_duid, facility_codes)])
