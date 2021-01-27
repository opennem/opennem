"""
OpenNEM v2 schema loader
"""


from typing import Dict, List

from opennem.core.compat.schema import OpennemDataSetV2, OpennemDataV2


def load_statset_v2(statset: List[Dict]) -> List[OpennemDataV2]:
    return OpennemDataSetV2(data=[OpennemDataV2.parse_obj(i) for i in statset])
