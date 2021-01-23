"""
OpenNEM Diff Versions
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from opennem.api.export.map import StatType
from opennem.core.compat import translate_id_v3_to_v2
from opennem.db import SessionLocal
from opennem.db.models.opennem import NetworkRegion
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.http import http

logger = logging.getLogger("opennem.diff.versions")

BASE_URL_V2 = "https://data.opennem.org.au"
BASE_URL_V3 = "https://data.dev.opennem.org.au"

CUR_YEAR = datetime.now().year


def get_v2_url(
    stat_type: StatType, network_region: str, bucket_size: str = "daily", year: int = CUR_YEAR
) -> str:
    """
    get v2 url

    https://data.opennem.org.au/power/tas1.json
    https://data.opennem.org.au/tas1/energy/daily/2021.json
    https://data.opennem.org.au/tas1/energy/monthly/all.json
    """

    url_components = []

    if stat_type == StatType.power:
        url_components = ["power", network_region.lower()]

    elif stat_type == StatType.energy and bucket_size == "monthly":
        url_components = [network_region.lower(), "energy", bucket_size, "all"]

    elif stat_type == StatType.energy and bucket_size == "daily":
        url_components = [network_region.lower(), "energy", bucket_size, str(year)]

    else:
        raise Exception("Invalid v2 url components")

    url_path = "/".join(url_components)
    url_path += ".json"

    url = urljoin(BASE_URL_V2, url_path)

    return url


def get_v3_url(
    stat_type: StatType, network_region: str, bucket_size: str = "daily", year: int = CUR_YEAR
) -> str:
    """
    Get v3 url

    https://data.dev.opennem.org.au/v3/stats/au/NEM/TAS1/power/7d.json
    https://data.dev.opennem.org.au/v3/stats/au/NEM/TAS1/energy/2021.json
    https://data.dev.opennem.org.au/v3/stats/au/NEM/TAS1/energy/all.json
    """

    url_components = [
        "v3",
        "stats",
        "au",
        "NEM",
        network_region.upper(),
        stat_type.value,
    ]

    if stat_type == StatType.power:
        url_components += [
            "7d",
        ]

    elif stat_type == StatType.energy and bucket_size == "monthly":
        url_components += ["all"]

    elif stat_type == StatType.energy and bucket_size == "daily":
        url_components += [str(year)]

    else:
        raise Exception("Invalid v2 url components")

    url_path = "/".join(url_components)
    url_path += ".json"

    url = urljoin(BASE_URL_V3, url_path)

    return url


class DiffComparisonSet(BaseConfig):
    stat_type: StatType
    network_region: str
    bucket_size: Optional[str]

    @property
    def urlv2(self) -> str:
        return get_v2_url(self.stat_type, self.network_region, self.bucket_size)

    @property
    def urlv3(self) -> str:
        return get_v3_url(self.stat_type, self.network_region, self.bucket_size)


def get_url_map(regions: List[NetworkRegion]) -> List[DiffComparisonSet]:
    urls = []

    for region in regions:
        a = DiffComparisonSet(stat_type=StatType.power, network_region=region.code, bucket_size="7d")
        urls.append(a)

        a = DiffComparisonSet(
            stat_type=StatType.energy, network_region=region.code, bucket_size="daily"
        )
        urls.append(a)

        a = DiffComparisonSet(
            stat_type=StatType.energy, network_region=region.code, bucket_size="monthly"
        )
        urls.append(a)

    return urls


def validate_url_map(url_map: List[DiffComparisonSet]) -> bool:
    success = True

    for us in url_map:
        for version in ["v2", "v3"]:
            req_url = getattr(us, f"url{version}")
            r = http.get(req_url)

            if not r.ok:
                logger.error("invalid {} url: {}".format(version, req_url))
                success = False

    return success


def get_network_regions(network: NetworkSchema) -> List[NetworkRegion]:
    """Return regions for a network"""
    s = SessionLocal()
    regions = s.query(NetworkRegion).filter_by(network_id=network.code).all()

    codes = [r.code for r in regions]

    return codes


def get_id_diff(seriesv2: Dict, seriesv3: Dict) -> Optional[List[str]]:
    id2_diffs = sorted([i["id"] for i in seriesv2])
    id3_diffs = sorted([translate_id_v3_to_v2(i["id"]) for i in seriesv3])

    diff = list(set(id2_diffs) - set(id3_diffs))

    if len(diff) < 1:
        return None

    return diff


def get_data_by_id(id: str, series: List[Dict]) -> Optional[Dict]:
    id_s = list(filter(lambda x: x["id"] == id, series))

    if len(id_s) < 1:
        logger.error("Could not find id {} in series".format(id))
        return None

    return id_s.pop()


def run_diff() -> None:
    regions = get_network_regions(NetworkNEM)
    statsetmap = get_url_map(regions)

    # validate all urls are valid
    validate_url_map(statsetmap)

    for statset in statsetmap:
        v2_power = http.get(statset.urlv2).json()
        v3_power = http.get(statset.urlv3).json()["data"]

        if len(v2_power) != len(v3_power):
            logger.info(
                "Series {} {} for {} is missing ids. v2 has {} v3 has {}".format(
                    statset.stat_type.value,
                    statset.bucket_size,
                    statset.network_region,
                    len(v2_power),
                    len(v3_power),
                )
            )

        id_diff = get_id_diff(v2_power, v3_power)

        if id_diff:
            for i in id_diff:
                logger.info(
                    "Series {} {} for {} is missing ids. v3 doesn't have {}".format(
                        statset.stat_type.value, statset.bucket_size, statset.network_region, i
                    )
                )


if __name__ == "__main__":
    run_diff()
