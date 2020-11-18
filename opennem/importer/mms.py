import csv
import json
import logging
from datetime import datetime
from functools import reduce
from itertools import groupby
from pathlib import Path
from typing import Optional

from opennem.core.facilitystatus import parse_facility_status
from opennem.core.loader import load_data
from opennem.core.normalizers import station_name_cleaner
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.schema.opennem import StationSchema
from opennem.schema.stations import StationSet

logger = logging.getLogger("opennem.importer.mms")


def parse_mms_date(date_string: str) -> Optional[datetime]:
    """

    `25/10/1998  12:00:00 am` => d

    """
    date_string_components = date_string.strip().split(" ")

    if len(date_string_components) < 2:
        raise Exception("Error parsing date: {}".format(date_string))

    date_part = date_string_components[0]

    dt = None

    try:
        dt = datetime.strptime(date_part, "%Y/%m/%d")
    except ValueError:
        raise Exception("Error parsing date: {}".format(date_string))

    # AEMO sets dates to this value when they mean None
    # if dt.year == 2999:
    # return None

    return dt


def dudetailsummary_grouper(tables):

    if "PARTICIPANT_REGISTRATION_DUDETAILSUMMARY" not in tables:
        raise Exception("No dudetailsummary table")

    records = tables["PARTICIPANT_REGISTRATION_DUDETAILSUMMARY"]

    mms = tables["mms"] if "mms" in tables else {}

    records = [
        {
            "date_start": parse_mms_date(i["START_DATE"]),
            "date_end": parse_mms_date(i["END_DATE"]),
            # "status": "operating",
            "code": i["DUID"],
            "network_region": i["REGIONID"],
            "station_code": i["STATIONID"],
            "participant_id": i["PARTICIPANTID"],
            "dispatch_type": i["DISPATCHTYPE"],
        }
        for i in records
    ]

    now = datetime.now()

    records = [
        {
            **i,
            "status": parse_facility_status("retired")
            if i["date_end"] <= now
            else parse_facility_status("operating"),
        }
        for i in records
    ]

    grouped_records = {}

    # First pass sorts facilities into stations
    for k, v in groupby(records, lambda x: (x["station_code"], x["code"])):
        key = k[0]
        duid = k[1]
        if key not in grouped_records:
            grouped_records[key] = {}
            grouped_records[key]["station_code"] = k[0]
            # grouped_records[key]["participant"] = v[0]["PARTICIPANTID"]
            grouped_records[key]["details"] = {}
            grouped_records[key]["facilities"] = []

        if duid not in grouped_records[key]["details"]:
            grouped_records[key]["details"][duid] = []

        grouped_records[key]["details"][duid] += list(v)

    # Second pass flatten the records and we should get start and end dates
    # and a derived status
    for rec in grouped_records.keys():
        for _, facility_group_records in grouped_records[rec][
            "details"
        ].items():

            # date_end_min = min(
            #     facility_group_records, key=lambda x: x["date_end"]
            # )
            date_end_max = max(
                facility_group_records, key=lambda x: x["date_end"]
            )
            date_start_min = min(
                facility_group_records, key=lambda x: x["date_start"]
            )

            grouped_rec = {
                **date_end_max,
                "date_start": date_start_min["date_start"],
            }

            if grouped_rec["date_end"].year == 2999:
                grouped_rec["date_end"] = None

            grouped_records[rec]["facilities"].append(grouped_rec)

    grouped_records = [
        {"station_code": i, "facilities": v["facilities"]}
        for i, v in grouped_records.items()
    ]

    tables["PARTICIPANT_REGISTRATION_DUDETAILSUMMARY"] = grouped_records

    for record in grouped_records:
        station_code = record["station_code"]

        if station_code not in mms:
            print("dudetailsummary: {} not in mms".format(station_code))
            continue

        # mms[station_code] = {**record, **mms[station_code]}
        mms[station_code]["facilities"] = record["facilities"]

    tables["mms"] = mms

    return tables


def operatingstatus_grouper(tables):

    if "PARTICIPANT_REGISTRATION_STATIONOPERATINGSTATUS" not in tables:
        raise Exception(
            "No PARTICIPANT_REGISTRATION_STATIONOPERATINGSTATUS table"
        )

    records = tables["PARTICIPANT_REGISTRATION_STATIONOPERATINGSTATUS"]

    mms = tables["mms"] if "mms" in tables else {}

    records = [
        {
            "effective_date": parse_mms_date(i["EFFECTIVEDATE"]),
            "station_code": i["STATIONID"],
            "status": i["STATUS"],
        }
        for i in records
    ]

    grouped_records = {}

    for station_code, records in groupby(records, lambda x: x["station_code"]):
        if station_code not in grouped_records:
            grouped_records[station_code] = {}
            grouped_records[station_code]["id"] = station_code
            grouped_records[station_code]["details"] = []

        grouped_records[station_code]["details"] += list(records)

    for station_code, record in grouped_records.items():
        date_max = max(record["details"], key=lambda x: x["effective_date"])
        grouped_records[station_code]["status"] = date_max["status"]
        # grouped_records[station_code]["status"] = date_max["status"]

        if station_code not in mms:
            print("operatingstatus: {} is not in MMS".format(station_code))

        mms[station_code]["status"] = date_max["status"]

    tables["PARTICIPANT_REGISTRATION_STATIONOPERATINGSTATUS"] = grouped_records

    tables["mms"] = mms

    return tables


def stations_grouper(tables):

    if "PARTICIPANT_REGISTRATION_STATION" not in tables:
        raise Exception("No PARTICIPANT_REGISTRATION_STATION table")

    records = tables["PARTICIPANT_REGISTRATION_STATION"]

    mms = tables["mms"] if "mms" in tables else {}

    records = [
        {
            "id": _id,
            "updated_at": parse_mms_date(i["LASTCHANGED"]),
            "name": station_name_cleaner(i["STATIONNAME"]),
            "code": i["STATIONID"],
            "station_code": i["STATIONID"],
            "network_name": i["STATIONNAME"],
            "address1": i["ADDRESS1"],
            "address2": i["ADDRESS2"],
            "locality": i["CITY"],
            "state": i["STATE"],
            "postcode": i["POSTCODE"],
            "facilities": [],
        }
        for _id, i in enumerate(records, start=1000)
    ]

    for record in records:
        station_code = record["station_code"]

        if station_code not in mms:
            mms[station_code] = {}

        mms[station_code] = record

    tables["mms"] = mms

    return tables


def dudetail_grouper(tables):

    if "PARTICIPANT_REGISTRATION_DUDETAIL" not in tables:
        raise Exception("No PARTICIPANT_REGISTRATION_DUDETAIL table")

    records = tables["PARTICIPANT_REGISTRATION_DUDETAIL"]

    mms = tables["mms"] if "mms" in tables else {}

    records = [
        {
            "code": i["DUID"],
            "version": i["VERSIONNO"],
            "capacity_registered": float(i["REGISTEREDCAPACITY"]),
            "capacity_maximum": float(i["MAXCAPACITY"]),
            "dispatch_type": i["DISPATCHTYPE"],
        }
        for _id, i in enumerate(records, start=1000)
    ]

    grouped_records = {}

    for network_code, records in groupby(records, lambda x: x["code"]):
        if network_code not in grouped_records:
            grouped_records[network_code] = {}
            grouped_records[network_code]["details"] = []

        grouped_records[network_code]["details"] += list(records)

    for network_code, record in grouped_records.items():
        version_max = max(record["details"], key=lambda x: x["version"])

        dudetail_record = {
            "capacity_registered": version_max["capacity_registered"],
            "capacity_maximum": version_max["capacity_maximum"],
        }

        facility = None

        for station_code in mms.keys():

            for fac in mms[station_code]["facilities"]:
                if fac["code"] == network_code:

                    # don't need the version field any more
                    fac.pop("version", None)

                    facility = {
                        **fac,
                        **dudetail_record,
                    }
                    fac_index = mms[station_code]["facilities"].index(fac)
                    mms[station_code]["facilities"][fac_index] = facility

        if not facility:
            print("dudetail: couldn't find facility: {}".format(network_code))

    tables["PARTICIPANT_REGISTRATION_DUDETAIL"] = grouped_records

    tables["mms"] = mms

    return tables


def genunits_grouper(tables):
    table_name = "PARTICIPANT_REGISTRATION_GENUNITS"

    if table_name not in tables:
        raise Exception("no genunits table")

    records = tables[table_name]

    records = [
        {
            "network_genset": i["GENSETID"],
            "emissions_factor_co2": float(i["CO2E_EMISSIONS_FACTOR"]),
        }
        for _, i in enumerate(records)
        if i["CO2E_EMISSIONS_FACTOR"]
    ]

    mms = tables["mms"] if "mms" in tables else {}

    # grouped_records = {}
    for record in records:
        facility_code = record["network_genset"]

        facility = None

        for station_code in mms.keys():
            for fac in mms[station_code]["facilities"]:
                if fac["code"] == facility_code:

                    facility = {
                        **fac,
                        **record,
                    }
                    fac_index = mms[station_code]["facilities"].index(fac)
                    # print(
                    #     "{} => {}".format(
                    #         station_code, record["emissions_factor_co2"]
                    #     )
                    # )
                    mms[station_code]["facilities"][fac_index][
                        "emissions_factor_co2"
                    ] = record["emissions_factor_co2"]

        if not facility:
            print("dudetail: couldn't find facility: {}".format(facility_code))

    tables[table_name] = records

    tables["mms"] = mms

    return tables


def load_aemo_csv(item, filename):

    if not item:
        item = {}

    if type(item) is not dict:
        raise Exception(
            "Invalid item type expecting a dict so we can fill it "
        )

    current_item = load_data(filename, True, content_type="latin-1")

    if "content" not in current_item:
        logger.error("No content in item to parse")
        return item

    content = current_item["content"]
    del current_item["content"]

    table_name = None
    table_values = ""
    table_fields = []
    table_records = []

    content_split = content.splitlines()

    datacsv = csv.reader(content_split)

    for row in datacsv:
        if not row or type(row) is not list or len(row) < 1:
            continue

        record_type = row[0]

        if record_type == "C":
            # @TODO csv meta stored in table
            if table_name is not None:
                item[table_name] = table_records

        elif record_type == "I":
            if table_name is not None:
                item[table_name] = table_records

            table_name = "{}_{}".format(row[1], row[2])
            table_fields = row[4:]
            table_records = []

        elif record_type == "D":
            table_values = row[4:]
            record = dict(zip(table_fields, table_values))
            table_records.append(record)

    return item


def load_mms_tables():
    mms_path = Path(__file__).parent.parent / "data" / "mms"

    mms_files = [
        "mms/{}".format(f.name)
        for f in mms_path.iterdir()
        if f.suffix in [".zip"]
    ]

    tables = reduce(load_aemo_csv, mms_files, {})

    return tables


def mms_import():
    tables = load_mms_tables()

    logger.info(
        "Imported {} tables: {}".format(
            len(tables.keys()), ", ".join(list(tables.keys()))
        )
    )

    tables = stations_grouper(tables)
    tables = dudetailsummary_grouper(tables)
    tables = operatingstatus_grouper(tables)
    tables = dudetail_grouper(tables)
    tables = genunits_grouper(tables)

    _mms = tables["mms"]

    mms = StationSet()

    for s in _mms.values():
        mms.add_dict(s)

    return mms


def mms_station_map_from_records(mms):
    """
    Get the station to duid map from MMS and return it
    """

    mms_duid_station_map = {}

    for station_record in mms.as_list():
        for network_code in [i.code for i in station_record.facilities]:
            mms_duid_station_map[network_code] = station_record.code

    return mms_duid_station_map


def mms_export():
    """

    Export MMS records

    @TODO move this to opennem.export and keep modules consistent
    """
    mms = mms_import()

    mms_duid_station_map = mms_station_map_from_records(mms)

    with open("data/mms.json", "w") as fh:
        fh.write(mms.json(indent=4))

    with open("data/mms_duid_station_map.json", "w") as fh:
        json.dump(mms_duid_station_map, fh, indent=4, cls=OpenNEMJSONEncoder)


if __name__ == "__main__":
    mms_export()
