"""
OpenNEM Diff Versions
"""

import glob
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

from opennem.api.export.map import StatType
from opennem.api.stats.loader import load_statset
from opennem.api.stats.schema import OpennemData, OpennemDataSet
from opennem.core.compat.loader import load_statset_v2
from opennem.core.compat.schema import OpennemDataSetV2, OpennemDataV2
from opennem.core.compat.utils import translate_id_v2_to_v3
from opennem.db import SessionLocal
from opennem.db.models.opennem import NetworkRegion
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.http import http
from opennem.utils.series import series_are_equal, series_not_close

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

    v2: Optional[OpennemDataSetV2]
    v3: Optional[OpennemDataSet]

    @property
    def urlv2(self) -> str:
        return get_v2_url(self.stat_type, self.network_region, self.bucket_size)

    @property
    def urlv3(self) -> str:
        return get_v3_url(self.stat_type, self.network_region, self.bucket_size)


def get_url_map(regions: List[NetworkRegion]) -> List[DiffComparisonSet]:
    urls = []

    for region in regions:
        a = DiffComparisonSet(
            stat_type=StatType.power, network_region=region.code, bucket_size="7d"
        )
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


def load_url_map(url_map: List[DiffComparisonSet]) -> List[DiffComparisonSet]:

    for us in url_map:
        for version in ["v2", "v3"]:
            req_url = getattr(us, f"url{version}")
            r = http.get(req_url)

            if not r.ok:
                logger.error("invalid {} url: {}".format(version, req_url))

            statset = None

            if version == "v2":
                statset = load_statset_v2(r.json())
                us.v2 = statset

            else:
                statset = load_statset(r.json())
                us.v3 = statset

    return url_map


def get_network_regions(
    network: NetworkSchema, network_region: Optional[str] = None
) -> List[NetworkRegion]:
    """Return regions for a network"""
    s = SessionLocal()
    regions = s.query(NetworkRegion).filter_by(network_id=network.code)

    if network_region:
        regions = regions.filter_by(code=network_region)

    regions = regions.all()

    return regions


def get_id_diff(seriesv2: OpennemDataV2, seriesv3: OpennemData) -> Optional[List[str]]:
    id2_diffs = sorted([i.id for i in seriesv2])
    id3_diffs = sorted([i.id_v2() for i in seriesv3])

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
    regions = get_network_regions(NetworkNEM, "NSW1")
    statsetmap = get_url_map(regions)

    # load urls
    statsetmap = load_url_map(statsetmap)

    # filter it down for now
    # statsetmap_power = list(filter(lambda x: x.stat_type == StatType.power, statsetmap))

    for statset in statsetmap:
        if not statset.v2 or not statset.v3:
            logger.error("Error getting schemas for v2 or v3")
            continue

        logger.info(
            "Comparing {} {} for {}".format(
                statset.stat_type.value, statset.bucket_size, statset.network_region
            )
        )
        logger.info(statset.urlv2)
        logger.info(statset.urlv3)

        if len(statset.v2.data) != len(statset.v2.data):
            logger.info(
                "Series {} {} for {} is missing ids. v2 has {} v3 has {}".format(
                    statset.stat_type.value,
                    statset.bucket_size,
                    statset.network_region,
                    len(statset.v2.data),
                    len(statset.v3.data),
                )
            )

        id2_diffs = sorted([i.id for i in statset.v2.data])
        id3_diffs = sorted([i.id_v2() for i in statset.v3.data])

        logger.info("v2 has ids:")
        for i in id2_diffs:
            logger.info("\t{}".format(i))

        logger.info("v3 has ids:")
        for i in id3_diffs:
            logger.info("\t{}".format(i))

        id_diff = list(set(id2_diffs) - set(id3_diffs))

        if len(id_diff) > 0:
            for i in id_diff:
                logger.info(
                    "Series {} {} for {} is missing ids. v3 doesn't have {}".format(
                        statset.stat_type.value, statset.bucket_size, statset.network_region, i
                    )
                )

        logger.info("Comparing each id field")

        for i in id2_diffs:
            logger.info(" = comparing {}".format(i))

            v2i = statset.v2.get_id(i)
            v3i = statset.v3.get_id(translate_id_v2_to_v3(i))

            if not v3i:
                logger.error("   missing in v3: {}".format(translate_id_v2_to_v3(i)))
                continue

            if not v2i:
                logger.error("    error getting id {} from v2".format(i))
                continue

            if v2i.fuel_tech:
                if v2i.fuel_tech == v3i.fueltech_v2():
                    logger.info("  * fueltech matches")
                else:
                    logger.error(
                        "  * fueltech DOESNT MATCH: {} and {}".format(
                            v2i.fuel_tech, v3i.fueltech_v2()
                        )
                    )

            if v2i.history:
                logger.info("  * comparing history:")

                if len(v2i.history.data) != len(v3i.history.data):
                    logger.error(
                        "    - data length mismatch v2 {} v3 {}".format(
                            len(v2i.history.data), len(v3i.history.data)
                        )
                    )

                data_matches = series_are_equal(v2i.history.values(), v3i.history.values())

                if False in list(data_matches.values()):
                    logger.error("    - values don't match ")

                    mismatch_values = series_not_close(v2i.history.values(), v3i.history.values())

                    extra_part = i.split(".")[1]

                    file_components = [
                        statset.stat_type.value,
                        statset.network_region,
                        statset.bucket_size,
                        extra_part,
                        v3i.fueltech_v2(),
                    ]

                    filename = "-".join([i for i in file_components if i])

                    with open(
                        f"diff_outs/{filename}-diff.json",
                        "w",
                    ) as fh:
                        json.dump(mismatch_values, fh, cls=OpenNEMJSONEncoder, indent=4)

                elif data_matches.keys() and len(data_matches.keys()):
                    logger.info(
                        "     - series values match {} values between {} and {}".format(
                            len(data_matches.keys()),
                            min(data_matches.keys()),
                            max(data_matches.keys()),
                        )
                    )

            # remaining attributes
            for v2ikey in v2i.dict().keys():
                if v2ikey in ["id", "fuel_tech", "history", "forecast"]:
                    continue

                if not hasattr(v3i, v2ikey):
                    logger.error("  * key {} is missing".format(v2ikey))
                else:
                    data_matches = getattr(v2i, v2ikey) == getattr(v3i, v2ikey)

                    if data_matches:
                        logger.info("  * key {} exists and matches ".format(v2ikey))
                    else:
                        logger.error(
                            "  * key {} DOESNT MATCH. values: v2'{}' and v3'{}'".format(
                                v2ikey, getattr(v2i, v2ikey), getattr(v3i, v2ikey)
                            )
                        )

        logger.info("=" * 50)


def run_data_diff() -> None:
    regions = get_network_regions(NetworkNEM, "NSW1")
    statsetmap = get_url_map(regions)

    # validate all urls are valid
    validate_url_map(statsetmap)
    statsetmap = load_url_map(statsetmap)

    for statset in statsetmap:
        print("{} {} {} ".format(statset.stat_type, statset.bucket_size, statset.network_region))
        print(statset.v2)
        print(statset.v3)


if __name__ == "__main__":

    files = glob.glob("diff_outs/*")

    for f in files:
        os.remove(f)
        logger.debug(f"Deleted {f}")

    run_diff()
