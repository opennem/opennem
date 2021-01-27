"""
OpenNEM Stat Set Loader

Takes a stat set or data history from exports in Dict form and returns
schemas.

"""
from typing import Any, Dict

from opennem.api.stats.schema import OpennemDataSet


def load_statset(stat_set: Dict[str, Any]) -> OpennemDataSet:
    """ """

    ds = OpennemDataSet.parse_obj(stat_set)

    return ds
