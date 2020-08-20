"""
    Parse current and v3 facilities registries and take a diff.


"""

import csv
import json
import logging
from datetime import timedelta
from itertools import chain
from operator import itemgetter
from pprint import pprint

from mdutils.mdutils import MdUtils

from opennem.utils.log_config import logging

from .loader import load_current, load_registry

logger = logging.getLogger("opennem.diff")

markdown_report = []


def run_diff():
    diff_report = {}

    registry = load_registry()
    current = load_current()

    registry_units = list(chain(*[s.facilities for s in registry]))
    current_units = list(chain(*[s.facilities for s in current]))

    registry_station_codes = [station.code for station in registry]
    current_station_codes = [station.code for station in current]

    registry_station_names = [station.name for station in registry]
    current_station_names = [station.name for station in current]

    new_stations = list(
        set(
            [
                station.name
                for station in current
                if station.name not in registry_station_names
                and station.code not in registry_station_codes
            ]
        )
    )

    md = MdUtils(file_name="data/diff_report.md", title="Opennem Report")
    md.new_header(level=1, title="Opennem Report")

    summary = ["", "Prod", "Version 3"]
    summary.extend(["Stations", str(len(registry)), str(len(current))])
    summary.extend(
        ["Units", str(len(registry_units)), str(len(current_units))]
    )

    md.new_table(columns=3, rows=3, text=summary)

    md.create_md_file()
    pprint(diff_report)


def run_diff_old():
    current = load_registry()
    v3 = load_current()

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
    add(" # Facility duids in current not in v3")
    add("")

    facility_duid_diff = list(
        set([i[4] for i in current]) - set([i[5] for i in v3])
    )

    add(facility_duid_diff, True)

    add(" # Fueltech Changes")
    add("")

    facility_duid_diff = list(
        set([(i[4], i[5]) for i in current]) - set([(i[5], i[6]) for i in v3])
    )

    add(facility_duid_diff, True)

    with open("data/diff_report.md", "w") as fh:
        fh.write("\n".join(markdown_report))


if __name__ == "__main__":
    run_diff()
