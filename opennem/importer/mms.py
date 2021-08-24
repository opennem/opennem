import json
import logging

from opennem.core.facilitystatus import parse_facility_status
from opennem.core.loader import load_data
from opennem.core.normalizers import station_name_cleaner
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.schema.stations import StationSet

logger = logging.getLogger("opennem.importer.mms")


def mms_import() -> StationSet:

    mms = StationSet()

    # for s in _mms.values():
    #     mms.add_dict(s)

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

    with open("data/mms2.json", "w") as fh:
        fh.write(mms.json(indent=4))

    # with open("data/mms_duid_station_map.json", "w") as fh:
    #     json.dump(mms_duid_station_map, fh, indent=4, cls=OpenNEMJSONEncoder)


if __name__ == "__main__":
    mms_export()
