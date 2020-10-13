from collections import OrderedDict
from datetime import datetime
from itertools import groupby
from operator import attrgetter
from typing import List, Optional

from sqlalchemy.orm import Session

from opennem.db.models.opennem import FacilityScada, Station
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval, TimePeriod
from opennem.schema.units import UnitDefinition
from opennem.utils.time import human_to_timedelta
from opennem.utils.timezone import make_aware

from .schema import (
    DataQueryResult,
    OpennemData,
    OpennemDataHistory,
    OpennemDataSet,
)


def stats_factory(
    stats: List[DataQueryResult],
    interval: TimeInterval,
    period: TimePeriod,
    network: NetworkSchema,
    units: UnitDefinition,
    code: str = None,
    region: str = None,
) -> Optional[OpennemDataSet]:
    """
        Takes a list of data query results and returns OpennemDataSets

        @TODO optional groupby field
        @TODO override timezone
    """

    network_timezone = network.get_timezone()

    dates = [s.interval for s in stats]
    start = make_aware(min(dates), network_timezone)
    end = make_aware(max(dates), network_timezone)

    # free
    dates = []

    group_codes = list(set([i.group_by for i in stats if i.group_by]))

    stats_grouped = []

    for group_code in group_codes:

        data_grouped = dict()

        for key, v in groupby(stats, attrgetter("interval")):
            if key not in data_grouped:
                data_grouped[key] = None

            value = list(v).pop()

            if value.group_by == group_code:
                data_grouped[key] = value.result

        data_sorted = OrderedDict(sorted(data_grouped.items()))

        history = OpennemDataHistory(
            start=start,
            last=end,
            interval=interval.interval_human,
            data=list(data_sorted.values()),
        )

        data = OpennemData(
            network=network.code,
            data_type=units.unit_type,
            units=units.unit,
            code=group_code,
            history=history,
        )

        stats_grouped.append(data)

    stat_set = OpennemDataSet(
        data_type=units.unit_type,
        data=stats_grouped,
        interval=interval,
        period=period,
        code=code,
        region_code=region,
        network=network.code,
    )

    return stat_set


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

        facility.scada_power = stats_factory(facility_power)

    return station
