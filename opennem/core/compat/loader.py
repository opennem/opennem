"""
OpenNEM v2 schema loader
"""

import logging
from datetime import timedelta

from opennem.api.export.map import StatType
from opennem.core.compat.schema import OpennemDataSetV2, OpennemDataV2
from opennem.diff.versions import get_v2_url
from opennem.schema.flows import FlowType
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import get_last_complete_day_for_network
from opennem.utils.http import http

logger = logging.getLogger("opennem.compat.loader")


def load_statset_v2(statset: list[dict]) -> OpennemDataSetV2:
    return OpennemDataSetV2(data=[OpennemDataV2.parse_obj(i) for i in statset])


def statset_patch(ds: OpennemDataSetV2, bucket_size: str) -> OpennemDataSetV2:
    """Patch fix for today()"""
    today = get_last_complete_day_for_network(NetworkNEM)

    ds_out = ds.copy()
    ds_out.data = []

    for ft in [FlowType.imports, FlowType.exports]:
        for st in [StatType.energy, StatType.marketvalue, StatType.emissions]:
            search_id_match = f"{ft.value}.{st.value}"

            dsid = ds.search_id(search_id_match)

            if not dsid:
                continue

            if bucket_size == "daily":
                if dsid.history.last != today:
                    day_gap = today - dsid.history.last
                    dsid.history.start = str(dsid.history.start + timedelta(days=day_gap.days))
                    dsid.history.last = str(today - timedelta(days=1))

            ds_out.data.append(dsid)

    return ds_out


def get_dataset(
    stat_type: StatType,
    network_region: str,
    bucket_size: str = "daily",
    year: int | None = None,
    testing: bool = True,
) -> OpennemDataSetV2:
    req_url = get_v2_url(stat_type, network_region, bucket_size, year, testing=testing)

    r = http.get(req_url)

    logger.debug(f"Loading: {req_url}")

    if not r.ok:
        raise Exception(f"Could not parse URL: {req_url}")

    json_data = r.json()

    statset = load_statset_v2(json_data)

    statset = statset_patch(statset, bucket_size=bucket_size)

    return statset


if __name__ == "__main__":
    ds = get_dataset(StatType.energy, "NSW1", "daily")

    with open("flow_test.json", "w") as fh:
        fh.write(ds.json())
