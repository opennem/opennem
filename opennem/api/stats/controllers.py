from collections import OrderedDict
from datetime import datetime, timezone
from textwrap import dedent
from typing import List, Optional, Union

from pytz import timezone as pytz_timezone
from sqlalchemy.orm import Session

from opennem.db import get_database_engine
from opennem.db.models.opennem import FacilityScada, Station
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.schema.units import UnitDefinition
from opennem.utils.cache import cache_scada_result
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


def stats_factory(
    stats: List[DataQueryResult],
    interval: TimeInterval,
    units: UnitDefinition,
    period: Optional[TimePeriod] = None,
    network: Optional[NetworkSchema] = None,
    timezone: Optional[Union[timezone, pytz_timezone]] = None,
    code: Optional[str] = None,
    region: Optional[str] = None,
    fueltech_group: Optional[bool] = False,
    group_field: Optional[str] = None,
    data_id: Optional[str] = None,
) -> Optional[OpennemDataSet]:
    """
        Takes a list of data query results and returns OpennemDataSets

        @TODO optional groupby field
        @TODO override timezone
    """

    if network:
        timezone = network.get_timezone()

    dates = [s.interval for s in stats]

    start = min(dates)
    end = max(dates)

    # should probably make sure these are the same TZ
    if timezone and not is_aware(start):
        start = make_aware(min(dates), timezone)

    if timezone and not is_aware(end):
        end = make_aware(max(dates), timezone)

    # free
    dates = []

    group_codes = list(set([i.group_by for i in stats if i.group_by]))

    stats_grouped = []

    for group_code in group_codes:

        data_grouped = dict()

        for stat in stats:
            if stat.interval not in data_grouped:
                data_grouped[stat.interval] = None

            if stat.group_by == group_code:
                data_grouped[stat.interval] = stat.result

        data_sorted = OrderedDict(sorted(data_grouped.items()))

        history = OpennemDataHistory(
            start=start,
            last=end,
            interval=interval.interval_human,
            data=list(data_sorted.values()),
        )

        data = OpennemData(
            data_type=units.unit_type,
            units=units.unit,
            code=group_code,
            interval=interval,
            period=period,
            history=history,
        )

        if network:
            data.network = network.code

        # *sigh* - not the most flexible model
        if fueltech_group:
            data.fuel_tech = group_code
            data.id = ".".join(
                [
                    network.code.lower(),
                    "fuel_tech",
                    group_code.lower(),
                    units.unit_type,
                ]
            )
            # @TODO make this an alias
            data.type = units.unit_type

        if group_field:
            group_fields = []

            # setattr(data, group_field, group_code)

            if network:
                group_fields.append(network.code.lower())

            group_fields = group_fields + [
                group_field,
                group_code,
                units.unit_type,
            ]

            data.id = ".".join([f for f in group_fields if f])
            data.type = units.unit_type

        if data_id:
            data.id = data_id

        if region:
            data.region = region

        stats_grouped.append(data)

    dt_now = datetime.now()

    if network:
        dt_now = dt_now.astimezone(network.get_timezone())

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


def networks_to_in(networks: List[NetworkSchema]):
    codes = ["'{}'".format(n.code) for n in networks]

    return ", ".join(codes)


@cache_scada_result
def get_scada_range(
    network: Optional[NetworkSchema] = None,
    networks: Optional[List[NetworkSchema]] = None,
    network_region: Optional[str] = None,
) -> ScadaDateRange:
    engine = get_database_engine()

    __query = """
        select
            min(fs.trading_interval)::timestamp AT TIME ZONE '{timezone}',
            max(fs.trading_interval)::timestamp AT TIME ZONE '{timezone}'
        from facility_scada fs
        where
            {network_query}
            {network_region_query}
            facility_code not like 'ROOFTOP_%%'
    """

    network_query = ""

    if network:
        network_query = f"fs.network_id = '{network.code}' and"

    if networks:
        network_query = "fs.network_id IN ({}) and ".format(
            networks_to_in(networks)
        )

    network_region_query = ""

    if network_region:
        # @TODO support network regions in scada_range
        # technically we don't need this atm
        pass
        # network_region_query = (
        # f"f.network_region = '{network_region.code}' and"
        # )

    scada_range_query = dedent(
        __query.format(
            network_query=network_query,
            network_region_query=network_region_query,
            timezone=network.timezone_database,
        )
    )

    with engine.connect() as c:
        scada_range_result = list(c.execute(scada_range_query))

        if len(scada_range_result) < 1:
            raise Exception("No scada range result")

        scada_min = scada_range_result[0][0]
        scada_max = scada_range_result[0][1]

    scada_range = ScadaDateRange(
        start=scada_min, end=scada_max, network=network
    )

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
        facility_power = list(
            filter(lambda s: s.facility_code == facility.code, stats)
        )

        # facility.scada_power = stats_factory(facility_power)

    return station
