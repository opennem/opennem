""" SQL query utilities """

from sqlalchemy.sql.functions import GenericFunction

from opennem.core.normalizers import normalize_duid


def duid_in_case(facility_codes: list[str]) -> str:
    """Converts a list of facility codes to an IN statement"""
    return ",".join([f"'{i}'" for i in map(normalize_duid, facility_codes)])


class time_bucket(GenericFunction):
    r"""Implement the ``CUBE`` grouping operation.
    This function is used as part of the GROUP BY of a statement,
    e.g. :meth:`_expression.Select.group_by`::
        stmt = select(
            func.sum(table.c.value), table.c.col_1, table.c.col_2
        ).group_by(func.cube(table.c.col_1, table.c.col_2))
    .. versionadded:: 1.2
    """
    _has_args = True
    inherit_cache = True


class time_bucket_gapfill(GenericFunction):
    r"""Implement the ``CUBE`` grouping operation.
    This function is used as part of the GROUP BY of a statement,
    e.g. :meth:`_expression.Select.group_by`::
        stmt = select(
            func.sum(table.c.value), table.c.col_1, table.c.col_2
        ).group_by(func.cube(table.c.col_1, table.c.col_2))
    .. versionadded:: 1.2
    """
    _has_args = True
    inherit_cache = True
