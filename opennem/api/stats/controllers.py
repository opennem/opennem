from datetime import datetime
from decimal import Decimal
from itertools import groupby
from operator import attrgetter, itemgetter
from typing import List, Optional

from sqlalchemy.orm import Session

from opennem.core.networks import network_from_network_code
from opennem.db.models.opennem import FacilityScada, Station
from opennem.schema.network import NetworkSchema
from opennem.schema.time import TimeInterval
from opennem.utils.time import human_to_timedelta
from opennem.utils.timezone import make_aware

from .schema import (
    DataQueryResult,
    OpennemData,
    OpennemDataHistory,
    OpennemDataSet,
)


def stats_set_factory(
    stats: List[OpennemData], code: str = None, network: str = None
) -> OpennemDataSet:
    stat_set = OpennemDataSet(
        data_type="power", data=stats, code=code, network=network
    )

    return stat_set


def stats_factory(
    stats: List[DataQueryResult],
    interval: TimeInterval,
    network: NetworkSchema,
    code: str = None,
) -> Optional[OpennemDataSet]:

    network_timezone = network.get_timezone()

    dates = [s.interval for s in stats]
    start = make_aware(min(dates), network_timezone)
    end = make_aware(max(dates), network_timezone)

    # free
    dates = []

    group_codes = list(set([i.group_by for i in stats if i.group_by]))

    stats_grouped = []

    for group_code in group_codes:

        data_grouped = {}

        for key, v in groupby(stats, attrgetter("interval")):
            if key not in data_grouped:
                data_grouped[key] = None

            value = list(v).pop()

            if value.group_by == group_code:
                data_grouped[key] = value.result

        history = OpennemDataHistory(
            start=start,
            last=end,
            interval=interval.interval_human,
            data=list(data_grouped.values()),
        )

        data = OpennemData(
            network=network.code,
            data_type="power",
            units="MW",
            code=group_code,
            history=history,
        )

        stats_grouped.append(data)

    stat_set = OpennemDataSet(
        data_type="power", data=stats_grouped, code=code, network=network.code
    )

    return stat_set


def station_attach_stats(station: Station, session: Session) -> Station:
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
