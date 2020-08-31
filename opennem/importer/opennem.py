import json
import os
from typing import List

import dictdiffer
from dictdiffer import diff

from opennem.core import load_data_csv
from opennem.core.facilitystatus import parse_facility_status
from opennem.core.loader import load_data
from opennem.db.models.opennem import Facility, Station
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.importer.compat import map_compat_facility_state
from opennem.schema.opennem import StationSchema
from opennem.utils.log_config import logging

from .aemo_gi import gi_import
from .aemo_rel import rel_import
from .mms import mms_import

logger = logging.getLogger("opennem.importer")

RECORD_MODEL_MAP = {
    "STATION": Station,
    "FACILITY": Facility,
}


def opennem_import():
    """
        Reads the OpenNEM data source

    """

    opennem_records = load_data_csv("opennem.csv")

    for rec in opennem_records:
        logger.debug(rec)

        if "record_type" not in rec:
            raise Exception("Invalid CSV: No record_type")

        record_type = rec["record_type"]

        if record_type not in RECORD_MODEL_MAP:
            raise Exception(
                "Invalid record type: {} is not a valid record type".format(
                    record_type
                )
            )

        record_model = RECORD_MODEL_MAP[record_type]

    return record_model


def record_diff(subject, comparitor):
    return {k: comparitor[k] for k in set(comparitor) - set(subject)}


def station_reindex(stations: List[dict]) -> List[dict]:
    """
        reindexes the opnnem formatted facilities from a list
        to a dict keyed by duid

    """
    stations_return = {}

    for station_code, station in stations.items():
        facs = []

        if "facilities" in station:
            facs = station.get("facilities")
            station.pop("facilities")

        fac_duids = [i["code"] for i in facs]

        if len(set(fac_duids)) != len(fac_duids):
            logger.info("Station {} has dupe duids".format(station_code))
            # raise Exception("error")

        station["facilities"] = {i.get("code"): i for i in facs}

        stations_return[station_code] = station

    return stations_return


def registry_to_opennem(registry_station):
    station = {
        "name": registry_station.get("display_name", ""),
        "code": registry_station.get("station_id", ""),
        "station_code": registry_station.get("station_id", ""),
        "lat": registry_station.get("location", {}).get("latitude", None),
        "lng": registry_station.get("location", {}).get("longitude", None),
        "facilities": [],
    }

    if not "duid_data" in registry_station:
        logger.info(
            "Registry: station has no duid data: {}".format(
                registry_station.get("display_name", "")
            )
        )
        return station

    for duid, registry_facility in registry_station["duid_data"].items():
        facility = {
            # "date_start": "1998-10-25T00:00:00",
            # "date_end": "2016-03-11T00:00:00",
            "code": duid,
            "network_region": registry_station.get("region_id", ""),
            "station_code": registry_station.get("station_id", ""),
            "dispatch_type": "GENERATOR",
            "status": parse_facility_status(
                map_compat_facility_state(
                    registry_station.get("status", {}).get("state", "")
                )
            ),
            "capacity_registered": registry_facility.get(
                "registered_capacity", None
            ),
        }
        station["facilities"].append(facility)

    return station


def opennem_import():
    """
        This is the main method that overlays AEMO data and produces facilities

    """
    log = []

    nem_mms = station_reindex(load_data("mms.json", from_project=True))
    nem_rel = station_reindex(load_data("rel.json", from_project=True))
    nem_gi = station_reindex(load_data("nem_gi.json", True))
    registry = load_data("facility_registry.json")

    opennem = nem_mms.copy()

    for station_code, rel_station in nem_rel.items():
        if station_code not in opennem.keys():
            logger.info("REL: New record {}".format(station_code))
            opennem[station_code] = rel_station

        else:
            logger.info("Existing record {}".format(station_code))
            om_station = opennem.get(station_code)

            for rel_facility_duid, rel_facility in rel_station[
                "facilities"
            ].items():

                if not rel_facility_duid:
                    continue

                if rel_facility_duid not in om_station["facilities"].keys():
                    logger.info(
                        " ==> Added duid {} to station ".format(
                            rel_facility_duid
                        )
                    )
                    om_station["facilities"][rel_facility_duid] = rel_facility
                    continue

                om_facility = om_station["facilities"][rel_facility_duid]

                if om_facility["status"]["code"] != "operating":
                    logger.info(
                        "Set status for {} to {}".format(
                            rel_facility_duid, "operating",
                        )
                    )
                    om_facility["status"]["code"] = "operating"
                    om_facility["status"]["label"] = "Operating"

                if rel_facility["fueltech"]:
                    logger.info(
                        "Set fueltech for {} to {}".format(
                            rel_facility_duid, rel_facility["fueltech"],
                        )
                    )
                    om_facility["fueltech_id"] = rel_facility["fueltech"]

                if (
                    rel_facility["capacity_registered"]
                    and rel_facility["capacity_registered"]
                    != om_facility["capacity_registered"]
                ):
                    logger.info(
                        "Set capacity for {} to {}".format(
                            rel_facility_duid,
                            rel_facility["capacity_registered"],
                        )
                    )
                    om_facility["capacity_registered"] = rel_facility[
                        "capacity_registered"
                    ]

    for station_code, gi_station in nem_gi.items():
        if station_code not in opennem.keys():
            logger.info("GI: New record {}".format(station_code))
            opennem[station_code] = gi_station

        else:
            logger.info("Existing record {}".format(station_code))
            om_station = opennem.get(station_code)

            for gi_facility_duid, gi_facility in gi_station[
                "facilities"
            ].items():

                if not gi_facility_duid:
                    continue

                if gi_facility_duid not in om_station["facilities"].keys():
                    logger.info(
                        " ==> Added duid {} to station ".format(
                            gi_facility_duid
                        )
                    )
                    om_station["facilities"][gi_facility_duid] = gi_facility
                    continue

                if (
                    gi_facility["status"]
                    and om_facility["status"]["code"] != gi_facility["status"]
                ):
                    logger.info(
                        "GI Set status for {} to {}".format(
                            rel_facility_duid, gi_facility["status"],
                        )
                    )
                    om_facility["status"] = parse_facility_status(
                        gi_facility["status"]
                    )

    for station_code, registry_station in registry.items():
        if station_code not in opennem.keys():
            if registry_station["location"]["state"] == "WA":
                logger.info("Registry: New record {}".format(station_code))
                opennem[station_code] = registry_to_opennem(registry_station)

            continue

        om_station = opennem.get(station_code)

        lat = registry_station.get("location", {}).get("latitude", None)
        lng = registry_station.get("location", {}).get("longitude", None)

        om_station["lat"] = lat
        om_station["lng"] = lng

        if lat and lng:
            logger.info(
                "Registry: set lat and lng for {}".format(station_code)
            )

    with open("data/opennem.json", "w") as fh:
        json.dump(opennem, fh, indent=4, cls=OpenNEMJSONEncoder)


def opennem_export():
    pass


if __name__ == "__main__":
    opennem_import()
