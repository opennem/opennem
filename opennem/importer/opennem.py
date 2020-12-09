import json
import logging
from typing import List

from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.loader import load_data
from opennem.db.models.opennem import Facility, Station
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.schema.opennem import StationSchema

from .aemo_gi import gi_import
from .aemo_rel import rel_import
from .mms import mms_import

logger = logging.getLogger("opennem.importer")

RECORD_MODEL_MAP = {
    "STATION": Station,
    "FACILITY": Facility,
}


def opennem_import_patches():
    """
    Reads the OpenNEM data source

    """

    opennem_records = load_data("opennem.csv", from_project=True)

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

        # stations_return[station_code] = StationSchema(**station)
        stations_return[station_code] = station

    return stations_return


def opennem_import():
    """
    This is the main method that overlays AEMO data and produces facilities

    """
    log = []

    nem_mms = station_reindex(load_data("mms.json", from_project=True))
    nem_rel = station_reindex(load_data("rel.json", from_project=True))
    nem_gi = station_reindex(load_data("nem_gi.json", True))
    registry = station_reindex(load_data("registry.json", True))

    opennem = nem_mms.copy()

    # REL
    for station_code, rel_station in nem_rel.items():
        if station_code not in opennem.keys():
            logger.info("REL: New record {}".format(station_code))
            opennem[station_code] = rel_station

        else:
            logger.info("REL: Existing record {}".format(station_code))
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
                        "REL: Set status for {} to {}".format(
                            rel_facility_duid,
                            "operating",
                        )
                    )
                    om_facility["status"]["code"] = "operating"
                    om_facility["status"]["label"] = "Operating"

                if rel_facility["fueltech"]:
                    logger.info(
                        "REL: Set fueltech for {} to {}".format(
                            rel_facility_duid,
                            rel_facility["fueltech"],
                        )
                    )
                    om_facility["fueltech"] = rel_facility["fueltech"]

                if (
                    rel_facility["capacity_registered"]
                    and rel_facility["capacity_registered"]
                    != om_facility["capacity_registered"]
                ):
                    logger.info(
                        "REL: Set capacity for %s to %s",
                        rel_facility_duid,
                        rel_facility["capacity_registered"],
                    )
                    om_facility["capacity_registered"] = rel_facility[
                        "capacity_registered"
                    ]

    # GI
    for station_code, gi_station in nem_gi.items():
        if (
            station_code not in opennem.keys()
            and not facility_station_join_by_name(gi_station["name"])
        ):
            logger.info("GI: New record {}".format(station_code))
            gi_station["created_by"] = "aemo_gi"
            opennem[station_code] = gi_station
            continue

        station_name = gi_station["name"]

        station_name_existing = list(
            filter(lambda x: x["name"] == gi_station["name"], opennem.values())
        )

        if len(station_name_existing) and facility_station_join_by_name(
            station_name
        ):
            station_code = station_name_existing[0]["code"]
            logger.info(
                "GI: found existing station we're joining to: {}".format(
                    station_code
                )
            )
        elif station_code not in opennem.keys():
            opennem[station_code] = gi_station

        logger.info("GI: Existing record {}".format(station_code))
        om_station = opennem.get(station_code)

        for gi_facility_duid, gi_facility in gi_station["facilities"].items():

            if not gi_facility_duid:
                continue

            if gi_facility_duid not in om_station["facilities"]:
                continue

            om_facility = om_station["facilities"][gi_facility_duid]

            if gi_facility_duid not in om_station["facilities"].keys():
                logger.info(
                    " ==> Added duid {} to station ".format(gi_facility_duid)
                )
                om_station["facilities"][gi_facility_duid] = gi_facility
                continue

            if (
                gi_facility["status"]
                and om_facility["status"]["code"] != gi_facility["status"]
            ):
                logger.info(
                    "GI Set status for {} to {}".format(
                        gi_facility_duid,
                        gi_facility["status"],
                    )
                )
                om_facility["status"] = gi_facility["status"]

            elif not om_facility["status"]:
                om_facility["status"] = gi_facility["status"]

            if not om_facility.get("fueltech", None):
                om_facility["fueltech"] = gi_facility["fueltech"]

    # registry
    for station_code, registry_station in registry.items():
        if station_code not in opennem.keys():
            if registry_station.get("state") == "WA":
                logger.info("Registry: New record {}".format(station_code))
                opennem[station_code] = registry_station

            continue

        om_station = opennem.get(station_code)

        lat = registry_station.get("lat", None)
        lng = registry_station.get("lng", None)

        om_station["lat"] = lat
        om_station["lng"] = lng

        if lat and lng:
            logger.info(
                "Registry: set lat and lng for {}".format(station_code)
            )

        for facility_code, registry_facility in registry_station.get(
            "facilities", {}
        ).items():

            if facility_code not in om_station["facilities"]:
                logger.info(
                    "Registry: {} has facility {} not in opennem".format(
                        station_code, facility_code
                    )
                )
                continue

            if (
                registry_facility["status"]
                and not om_station["facilities"][facility_code]["status"]
            ):
                logger.info(
                    "Registry: set status to {}".format(
                        registry_facility["status"]
                    )
                )
                om_station["facilities"][facility_code][
                    "status"
                ] = registry_station["status"]

            if registry_facility["fueltech"] and not om_station["facilities"][
                facility_code
            ].get("fueltech", None):
                om_station["facilities"][facility_code][
                    "fueltech"
                ] = registry_facility["fueltech"]

            logger.info(
                "registry: {} registry fueltech {} opennem fueltech {}".format(
                    facility_code,
                    registry_facility["fueltech"],
                    om_station["facilities"][facility_code].get(
                        "fueltech", None
                    ),
                )
            )

    for station_code, station_entry in opennem.items():
        facilities = [i for i in station_entry["facilities"].values()]
        opennem[station_code]["facilities"] = facilities

    with open("data/opennem.json", "w") as fh:
        json.dump(opennem, fh, indent=4, cls=OpenNEMJSONEncoder)

    stations = [StationSchema(**i) for i in list(opennem.values())]

    return stations


def opennem_export():
    pass


if __name__ == "__main__":
    opennem_import()
