""" Query utilities """
from opennem.core.normalizers import normalize_duid
from opennem.schema.network import NetworkSchema


def duid_to_case(facility_codes: list[str]) -> str:
    """Converts and normalizes list of facilities to in statement"""
    return ",".join([f"'{i}'" for i in map(normalize_duid, facility_codes)])


def networks_to_sql_in(networks: list[NetworkSchema]) -> str:
    codes = [f"'{n.code}'" for n in networks]

    return ", ".join(codes)


def list_to_case(list_: list[str]) -> str:
    """Converts a list of strings to a case statement"""
    return ",".join([f"'{i}'" for i in list_])


def list_to_sql_in_condition(codes: list[str]) -> str:
    """Convert a list of strings to a case statement"""
    return ",".join([f"'{i}'" for i in codes])
