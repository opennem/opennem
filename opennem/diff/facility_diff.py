"""
    Parse current and v3 facilities registries and take a diff.


"""

import csv
import json
import logging
import re
from datetime import timedelta
from itertools import chain
from operator import itemgetter
from pprint import pprint

from mdutils.mdutils import MdUtils

from opennem.utils.log_config import logging

from .loader import load_current, load_registry

logger = logging.getLogger("opennem.diff")

markdown_report = []


def report_changed_names(registry, current):
    renames = []

    for station in registry:
        in_current = list(filter(lambda x: x.code == station.code, current))

        if in_current and len(in_current):
            station_current = in_current[0]
            if station_current.name != station.name:
                renames.append(
                    "`{}` renamed to `{}`".format(
                        station.name, station_current.name
                    )
                )

    return renames


def report_changed_fueltechs(registry_units, current_units):
    renames = []

    for unit in registry_units:
        in_current = list(filter(lambda x: x.duid == unit.duid, current_units))

        if in_current and len(in_current):
            unit_current = in_current[0]
            if unit_current.fueltech != unit.fueltech:
                renames.append(
                    "{} (`{}`) fueltech `{}` changed to `{}`".format(
                        unit_current.name,
                        unit_current.duid,
                        unit_current.fueltech,
                        unit.fueltech,
                    )
                )

    return renames


def report_changed_capacities(registry_units, current_units):
    renames = []

    for unit in registry_units:
        in_current = list(filter(lambda x: x.duid == unit.duid, current_units))

        if in_current and len(in_current):
            unit_current = in_current[0]
            if unit_current.capacity == None and unit.capacity:
                renames.append(
                    "{} (`{}`) added capacity `{}`".format(
                        unit_current.name, unit_current.duid, unit.capacity,
                    )
                )
            elif (
                unit_current.capacity
                and unit.capacity
                and round(unit_current.capacity, 0) != round(unit.capacity, 0)
            ):
                renames.append(
                    "{} (`{}`) capacity `{}` changed to `{}`".format(
                        unit_current.name,
                        unit_current.duid,
                        unit_current.capacity,
                        unit.capacity,
                    )
                )

    return renames


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

    # Summary
    md.new_header(level=1, title="Summary")
    summary = ["", "Prod", "Version 3"]
    summary.extend(["Stations", str(len(registry)), str(len(current))])
    summary.extend(
        ["Units", str(len(registry_units)), str(len(current_units))]
    )
    md.new_table(columns=3, rows=3, text=summary)

    # Renames
    md.new_header(level=1, title="Renamed Stations")
    renames = report_changed_names(registry, current)
    md.new_list(renames)

    # Fueltechs
    md.new_header(level=1, title="Changed Fueltechs")
    renames = report_changed_fueltechs(registry_units, current_units)
    md.new_list(renames)

    # Capacities
    md.new_header(level=1, title="Changed Capacities")
    renames = report_changed_capacities(registry_units, current_units)
    md.new_list(renames)

    md.new_table_of_contents(table_title="Contents", depth=2)
    md.create_md_file()


def run_diff_old():
    current = load_registry()
    v3 = load_current()

    current_stations = list(set([i[1] for i in current]))
    v3_stations = list(set([i[2] for i in v3]))
    current_stations_names = list(set([i[0] for i in current]))
    v3_stations_names = list(set([i[0] for i in v3]))

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
