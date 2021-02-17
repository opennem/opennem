import logging
from collections import OrderedDict
from datetime import datetime, timezone
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

import pytz
from sqlalchemy.orm import Session

from opennem.core.normalizers import normalize_duid
from opennem.db import get_database_engine
from opennem.db.models.opennem import FacilityScada, Station
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.schema.units import UnitDefinition
from opennem.utils.cache import cache_scada_result
from opennem.utils.numbers import cast_trailing_nulls
from opennem.utils.time import human_to_timedelta
from opennem.utils.timezone import is_aware, make_aware
from opennem.utils.version import get_version

from .schema import (
    DataQueryResult,
    OpennemData,
    OpennemDataHistory,
    OpennemDataSet,
    ScadaDateRange,
)

logger = logging.getLogger(__name__)


def duid_in_case(facility_codes: List[str]) -> str:
    """Takes a list of duids and returns a formatted sql array for IN"""
    map_list = ["'{}'".format(i) for i in map(normalize_duid, facility_codes)]
    return ",".join(map_list)


def stats_factory(
    stats: List[DataQueryResult],
    units: UnitDefinition,
    interval: TimeInterval,
    period: Optional[TimePeriod] = None,
    network: Optional[NetworkSchema] = None,
    timezone: Optional[Union[timezone, str]] = None,
    code: Optional[str] = None,
    region: Optional[str] = None,
    include_group_code: bool = False,
    fueltech_group: Optional[bool] = False,
    group_field: Optional[str] = None,
    data_id: Optional[str] = None,
    localize: Optional[bool] = True,
) -> Optional[OpennemDataSet]:
    """
    Takes a list of data query results and returns OpennemDataSets

    @TODO optional groupby field
    @TODO multiple groupings / slight refactor

    """

    if network:
        timezone = network.get_timezone()

    group_codes = list(set([i.group_by for i in stats if i.group_by]))

    stats_grouped = []

    for group_code in group_codes:

        data_grouped: Dict[datetime, Any] = dict()

        for stat in stats:
            if stat.group_by != group_code:
                continue

            if stat.interval not in data_grouped:
                data_grouped[stat.interval] = None

            data_grouped[stat.interval] = stat.result

        data_sorted = OrderedDict(sorted(data_grouped.items()))

        data_value = list(data_sorted.values())

        # Skip null series
        if len([i for i in data_value if i]) == 0:
            continue

        # @TODO possible bring this back
        # Skip zero series
        # if sum([i for i in data_value if i]) == 0:
        # continue

        # Cast trailing nulls
        if not units.name.startswith("temperature") or units.cast_nulls:
            data_value = cast_trailing_nulls(data_value)

        # Find start/end dates
        dates = list(data_grouped.keys())

        if not dates:
            return None

        start = min(dates)
        end = max(dates)

        # should probably make sure these are the same TZ
        if localize:
            if timezone and not is_aware(start):
                start = make_aware(start, timezone)

            if timezone and not is_aware(end):
                end = make_aware(end, timezone)

            if timezone and localize and network and network.offset:
                tz = pytz.FixedOffset(int(network.offset))

                start = start.astimezone(tz)
                end = end.astimezone(tz)

        # free
        dates = []

        history = OpennemDataHistory(
            start=start,
            last=end,
            interval=interval.interval_human,
            data=data_value,
        )

        data = OpennemData(
            data_type=units.unit_type,
            units=units.unit,
            code=group_code,
            # interval=interval,
            # period=period,
            history=history,
        )

        if network:
            data.network = network.code.lower()

        # *sigh* - not the most flexible model
        # @TODO fix this schema and make it more flexible
        if fueltech_group:
            data.fuel_tech = group_code

            data_comps = [
                # @NOTE disable for now since FE doesn't
                # support it
                # network.country if network else None,
                network.code.lower() if network else None,
                region.lower() if region else None,
                "fuel_tech",
                group_code,
                units.unit_type,
            ]

            data.id = ".".join(i for i in data_comps if i)
            # @TODO make this an alias
            data.type = units.unit_type

        if group_field:
            group_fields = []

            # setattr(data, group_field, group_code)

            if network:
                group_fields.append(network.code.lower())

            if region:
                group_fields.append(region.lower())

            group_fields = group_fields + [
                units.unit_type,
                group_code if include_group_code else None,
                # group_field,
            ]

            data.id = ".".join([f for f in group_fields if f])
            data.type = units.unit_type

        if data_id:
            data.id = data_id

        if not data.id:
            _id_list = []

            # @NOTE disable for now since FE doesn't
            # support it
            # network.country if network else None,

            if network:
                _id_list.append(network.code.lower())

            if region:
                _id_list.append(region.lower())

            if group_code:
                _id_list.append(group_code.lower())

            if units and units.name_alias:
                _id_list.append(units.name_alias)
            elif units and units.name:
                _id_list.append(units.name)

            data.id = ".".join([f for f in _id_list if f])
            data.type = units.unit_type

        if region:
            data.region = region

        stats_grouped.append(data)

    dt_now = datetime.now()

    if network:
        dt_now = dt_now.astimezone(network.get_timezone())

    # @NOTE this should probably be
    # country.network.region
    if not code:
        if network:
            code = network.code

        if region:
            code = region

    stat_set = OpennemDataSet(
        type=units.unit_type,
        data=stats_grouped,
        created_at=dt_now,
        code=code,
        version=get_version(),
    )

    if network:
        stat_set.network = network.code

    if region:
        stat_set.region = region

    return stat_set


def networks_to_in(networks: List[NetworkSchema]) -> str:
    codes = ["'{}'".format(n.code) for n in networks]

    return ", ".join(codes)


SCADA_RANGE_EXCLUDE_DUIDS = [
    "V-SA",
    "V-SA-2",
    "N-Q-MNSP1",
    "N-Q-MNSP1-2",
    "NSW1-QLD1",
    "NSW1-QLD1-2",
    "V-S-MNSP1",
    "V-S-MNSP1-2",
    "T-V-MNSP1",
    "T-V-MNSP1-2",
    "VIC1-NSW1",
    "VIC1-NSW1-2",
]


@cache_scada_result
def get_scada_range(
    network: Optional[NetworkSchema] = None,
    networks: Optional[List[NetworkSchema]] = None,
    network_region: Optional[str] = None,
    facilities: Optional[List[str]] = None,
) -> Optional[ScadaDateRange]:
    """Get the start and end dates for a network query. This is more efficient
    than providing or querying the range at query time
    """
    engine = get_database_engine()

    __query = """
        select
            min(fs.trading_interval)::timestamp AT TIME ZONE '{timezone}',
            max(fs.trading_interval)::timestamp AT TIME ZONE '{timezone}'
        from facility_scada fs
        where
            {facility_query}
            {network_query}
            {network_region_query}
            facility_code not like 'ROOFTOP_%%'
            and facility_code not in ({exclude_duids})
            and is_forecast is False
            and generated > 0
    """

    network_query = ""
    timezone = "UTC"

    if network:
        network_query = f"fs.network_id = '{network.code}' and"
        # timezone = network.timezone_database

    if networks:
        net_case = networks_to_in(networks)
        network_query = "fs.network_id IN ({}) and ".format(net_case)

    network_region_query = ""

    if network_region:
        # @TODO support network regions in scada_range
        # technically we don't need this atm
        pass
        # network_region_query = (
        # f"f.network_region = '{network_region.code}' and"
        # )

    facility_query = ""

    if facilities:
        fac_case = duid_in_case(facilities)
        facility_query = "fs.facility_code IN ({}) and ".format(fac_case)

    exclude_duids = duid_in_case(SCADA_RANGE_EXCLUDE_DUIDS)

    scada_range_query = dedent(
        __query.format(
            facility_query=facility_query,
            network_query=network_query,
            network_region_query=network_region_query,
            timezone=timezone,
            exclude_duids=exclude_duids,
        )
    )

    with engine.connect() as c:
        logger.debug(scada_range_query)
        scada_range_result = list(c.execute(scada_range_query))

        if len(scada_range_result) < 1:
            raise Exception("No scada range result")

        scada_min = scada_range_result[0][0]
        scada_max = scada_range_result[0][1]

    if not scada_min or not scada_max:
        return None

    scada_range = ScadaDateRange(start=scada_min, end=scada_max, network=network)

    return scada_range


def station_attach_stats(station: Station, session: Session) -> Station:
    # @TODO update for new queries
    since = datetime.now() - human_to_timedelta("7d")

    facility_codes = list(set([f.code for f in station.facilities]))

    stats = (
        session.query(FacilityScada)
        .filter(FacilityScada.facility_code.in_(facility_codes))
        .filter(FacilityScada.trading_interval >= since)
        .order_by(FacilityScada.facility_code)
        .order_by(FacilityScada.trading_interval)
        .all()
    )

    for facility in station.facilities:
        facility_power = list(filter(lambda s: s.facility_code == facility.code, stats))

        # facility.scada_power = stats_factory(facility_power)

    return station
