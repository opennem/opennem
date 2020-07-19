"""
    Parse current and v3 facilities registries and take a diff.


"""

import csv
import json
import logging
from datetime import timedelta
from operator import itemgetter
from pprint import pprint

import requests
import requests_cache

logging.basicConfig(level=logging.INFO)


REQUESTS_CACHE_PATH = ".requests"
FACILITIES_CURRENT = (
    "https://data.opennem.org.au/facility/facility_registry.json"
)
FACILITIES_V3 = "https://s3-ap-southeast-2.amazonaws.com/data.opennem.org.au/v3/geo/au_facilities.json"


requests_cache.install_cache(
    REQUESTS_CACHE_PATH, expire_after=timedelta(days=60)
)


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


def main():
    fac_current = requests.get(FACILITIES_CURRENT).json()

    remapped = []

    for k, v in fac_current.items():
        for duid, fac in v["duid_data"].items():
            i = [
                v["display_name"],
                # k,
                normalize_regions(v["region_id"]),
                normalize_states(v["status"]["state"]),
                duid,
                fac["fuel_tech"] if "fuel_tech" in fac else None,
                fac["registered_capacity"]
                if "registered_capacity" in fac
                else None,
            ]
            remapped.append(i)

    remapped = sorted(remapped, key=itemgetter(1, 0))

    with open("data/facility_diff/facilities_current.csv", "w") as fh:
        csvwriter = csv.writer(fh)
        for line in remapped:
            csvwriter.writerow(line)

    fac_v3 = requests.get(FACILITIES_V3).json()

    fac_v3 = fac_v3["features"]
    remapped = []

    for f in fac_v3:
        for fac in f["properties"]["duid_data"]:
            i = [
                f["properties"]["name"],
                # fac["duid"],
                normalize_regions(f["properties"]["network_region"]),
                fac["status"].lower(),
                fac["duid"],
                fac["fuel_tech"] if "fuel_tech" in fac else None,
                fac["registered_capacity"]
                if "registered_capacity" in fac
                else None,
            ]
            remapped.append(i)

    remapped = sorted(remapped, key=itemgetter(1, 0))

    with open("data/facility_diff/facilities_v3.csv", "w") as fh:
        csvwriter = csv.writer(fh)
        for line in remapped:
            csvwriter.writerow(line)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("User interrupt")
