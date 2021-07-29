"""
OpenNEM v2 schema loader
"""
import logging
from typing import Dict, List, Optional

from opennem.api.export.map import StatType
from opennem.core.compat.schema import OpennemDataSetV2, OpennemDataV2
from opennem.diff.versions import get_v2_url
from opennem.utils.http import http

logger = logging.getLogger("opennem.compat.loader")


def load_statset_v2(statset: List[Dict]) -> OpennemDataSetV2:
    return OpennemDataSetV2(data=[OpennemDataV2.parse_obj(i) for i in statset])


def get_dataset(
    stat_type: StatType,
    network_region: str,
    bucket_size: str = "daily",
    year: Optional[int] = None,
) -> OpennemDataSetV2:
    req_url = get_v2_url(stat_type, network_region, bucket_size, year)

    r = http.get(req_url)

    logger.debug("Loading: {}".format(req_url))

    if not r.ok:
        raise Exception("Could not parse URL: {}".format(req_url))

    json_data = r.json()

    statset = load_statset_v2(json_data)

    return statset
