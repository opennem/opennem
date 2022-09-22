""" Query utilities """
from opennem.core.normalizers import normalize_duid


def duid_to_case(facility_codes: list[str]) -> str:
    return ",".join(["'{}'".format(i) for i in map(normalize_duid, facility_codes)])


def list_to_case_statement(codes: list[str]) -> str:
    """Convert a list of strings to a case statement"""
    return ",".join(["'{}'".format(i) for i in codes])
