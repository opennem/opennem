"""
    Parse current and v3 facilities registries and take a diff.


"""

import csv
import json
import logging
from datetime import timedelta
from operator import itemgetter
from pprint import pprint

from opennem.utils.log_config import logging

logger = logging.getLogger("opennem.diff")
logger.setLevel(logging.DEBUG)

logging.basicConfig(level=logging.INFO)


def normalize_states(state):
    state = state.lower()

    if state == "commissioned":
        return "operating"

    if state == "decommissioned":
        return "retired"

    return state


def normalize_regions(region):
    if region == "WA":
        return "WA1"

    return region


markdown_report = []


def get_maps():
    logger.info("Running facility diff")

    with open("opennem/db/fixtures/facility_registry.json") as fh:
        fac_current = json.load(fh)

    fac_current_remapped = []

    for k, v in fac_current.items():
        for duid, fac in v["duid_data"].items():
            i = [
                v["display_name"] or "",
                k,
                normalize_regions(v["region_id"]) or "",
                normalize_states(v["status"]["state"]),
                duid or "",
                fac["fuel_tech"] if "fuel_tech" in fac else "",
                fac["registered_capacity"]
                if "registered_capacity" in fac
                else 0,
            ]
            fac_current_remapped.append(i)

    fac_current_remapped = sorted(
        fac_current_remapped, key=itemgetter(2, 0, 4, 6)
    )

    with open("data/stations.geojson") as fh:
        fac_v3 = json.load(fh)

    fac_v3 = fac_v3["features"]
    fac_v3_remapped = []

    for f in fac_v3:
        for fac in f["properties"]["duid_data"]:
            i = [
                f["properties"]["name"] or "",
                # fac["duid"],
                f["properties"]["oid"],
                f["properties"]["station_code"] or "",
                normalize_regions(f["properties"]["network_region"])
                if "network_region" in f["properties"]
                else "",
                fac["status"].lower(),
                fac["duid"] or "",
                fac["fuel_tech"] if "fuel_tech" in fac else "",
                fac["registered_capacity"]
                if "registered_capacity" in fac
                else 0,
            ]
            fac_v3_remapped.append(i)

    fac_v3_remapped = sorted(fac_v3_remapped, key=itemgetter(3, 0, 5, 7))

    return fac_current_remapped, fac_v3_remapped


def add(line, check=False):
    if type(line) is list:
        for l in line:
            if check:
                l = " * {}".format(l)
            markdown_report.append(l)
    else:
        if check:
            line = " * {}".format(line)
        markdown_report.append(line)


def run_diff():
    current, v3 = get_maps()
    current_stations = list(set([i[1] for i in current]))
    v3_stations = list(set([i[2] for i in v3]))
    current_stations_names = list(set([i[0] for i in current]))
    v3_stations_names = list(set([i[0] for i in v3]))

    add("# Opennem Facility Diff Report")
    add("## Overview ")
    add(" * Current Stations: {}".format(len(current_stations)))
    add(" * v3 Stations: {}".format(len(v3_stations)))
    add(" * Current Facilities: {}".format(len(current)))
    add(" * v3 Facilities: {}".format(len(v3)))
    add("")
    add(" ## Station codes in current not in v3")
    add("")
    add(list(set(current_stations) - set(v3_stations)), True)
    add(" ## Stations in current not in v3")
    add("")
    add(list(set(current_stations_names) - set(v3_stations_names)), True)

    with open("data/diff_report.md", "w") as fh:
        fh.write("\n".join(markdown_report))


if __name__ == "__main__":
    run_diff()
