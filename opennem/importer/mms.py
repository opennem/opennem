import json
import logging

from opennem.core.facilitystatus import parse_facility_status
from opennem.core.loader import load_data
from opennem.core.normalizers import station_name_cleaner
from opennem.exporter.encoders import OpenNEMJSONEncoder
from opennem.schema.stations import StationSet

logger = logging.getLogger("opennem.importer.mms")


__query = """

select
    mms.station.stationid,
    mms.station.stationname,
    stationoperatingstatus.status,
    stationoperatingstatus.effectivedate as status_effectivedate,
    mms.station.address1,
    mms.station.address2,
    mms.station.city,
    mms.station.state,
    dualloc.gensetid,
    mms.dispatchableunit.duid,
    mms.dispatchableunit.duname,
    mms.dispatchableunit.unittype,
    mms.dudetail.registeredcapacity,
    mms.dudetail.maxcapacity,
    mms.genunits.co2e_emissions_factor,
    mms.genunits.co2e_data_source,
    mms.genunits.co2e_energy_source,
    1
from mms.dispatchableunit
left join (
    select
        duid,
        stationid,
        max(effectivedate)
    from mms.stadualloc
    group by 1, 2
    order by duid
) as stadualloc on stadualloc.duid = mms.dispatchableunit.duid
left join mms.station on stadualloc.stationid = mms.station.stationid
inner join (
    select
        stationid,
        status,
        max(effectivedate) as effectivedate
    from mms.stationoperatingstatus
    group by 1, 2 order by stationid
) as stationoperatingstatus on stationoperatingstatus.stationid = mms.station.stationid
left join (
    select
        duid,
        max(effectivedate),
        max(versionno) as versionno
    from mms.dudetail
    group by 1
    order by duid
) as dt on dt.duid = mms.dispatchableunit.duid
left join mms.dudetail on mms.dudetail.duid = dt.duid and mms.dudetail.versionno = dt.versionno
left join (
    select
        duid,
        gensetid,
        max(effectivedate) as effectivedate
    from mms.dualloc
    group by 1, 2
    order by duid, gensetid
) as dualloc on dualloc.duid = mms.dispatchableunit.duid
left join mms.genunits on mms.genunits.gensetid = dualloc.gensetid
order by 1 asc
;
"""


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
