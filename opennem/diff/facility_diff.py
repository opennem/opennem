"""
    Parse current and v3 facilities registries and take a diff.


"""

import csv
import json

# from opennem.utils.log_config
import logging
import re
from datetime import timedelta
from itertools import chain
from operator import itemgetter
from pprint import pprint
from typing import List

from mdutils.mdutils import MdUtils

from opennem.core.loader import load_data

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


def records_diff(
    subject: List[object], comparitor: List[object], key: str = "code"
) -> List[str]:
    diff_keys = list(
        set([getattr(i, key) for i in subject])
        - set([getattr(i, key) for i in comparitor])
    )

    diff_records = list(
        filter(lambda x: getattr(x, key) in diff_keys, subject)
    )

    return diff_records


def station_in_registry_not_in_new(registry, current):
    diff_stations = records_diff(registry, current)

    list_table = ["Name", "Code", "Facilities"]

    [
        list_table.extend([i.name, i.code, str(len(i.facilities))])
        for i in diff_stations
    ]

    return list_table


def stations_in_new_not_in_registry(registry, current):
    diff_stations = records_diff(current, registry)

    list_table = ["Name", "Code", "Facilities"]

    [
        list_table.extend(
            [i.name, str(i.code) if i.code else "", str(len(i.facilities))]
        )
        for i in diff_stations
    ]

    return list_table


get_num_rows = lambda records, columns: int(len(records) / columns)


def run_diff():
    diff_report = {}

    registry = load_registry()
    current = load_current()

    nem_mms = load_data("mms.json", True)
    nem_gi = load_data("nem_gi.json", True)
    nem_rel = load_data("rel.json", True)

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

    # Old stations not in new
    md.new_header(level=1, title="Stations not in current")
    not_in_news = station_in_registry_not_in_new(registry, current)
    md.new_table(
        columns=3,
        rows=get_num_rows(not_in_news, 3),
        text=not_in_news,
        text_align="left",
    )

    # Old stations not in new
    md.new_header(level=1, title="New Stations")
    not_in_registry = stations_in_new_not_in_registry(registry, current)
    md.new_table(
        columns=3,
        rows=get_num_rows(not_in_registry, 3),
        text=not_in_registry,
        text_align="left",
    )

    md.new_table_of_contents(table_title="Contents", depth=2)
    md.create_md_file()


if __name__ == "__main__":
    run_diff()
