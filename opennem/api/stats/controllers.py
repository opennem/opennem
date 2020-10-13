from datetime import datetime
from decimal import Decimal
from itertools import groupby
from operator import itemgetter
from typing import List, Optional

from sqlalchemy.orm import Session

from opennem.core.networks import network_from_network_code
from opennem.db.models.opennem import FacilityScada, Station
from opennem.schema.time import TimeInterval
from opennem.utils.time import human_to_timedelta

from .schema import OpennemData, OpennemDataHistory, OpennemDataSet


def stats_set_factory(
    stats: List[OpennemData], code: str = None, network: str = None
) -> OpennemDataSet:
    stat_set = OpennemDataSet(
        data_type="power", data=stats, code=code, network=network
    )

    return stat_set


def stats_factory(
    scada: List[FacilityScada],
    interval: TimeInterval,
    network_code: str = "NEM",
    code: str = None,
) -> Optional[OpennemData]:
    if len(scada) < 1:
        return None

    network_code = network_code.upper()

    network = network_from_network_code(network_code)
    network_timezone = network.get_timezone()

    dates = [s["trading_interval"] for s in scada]
    start = min(dates)
    end = max(dates)

    # pluck the list
    data = [
        {
            k: v
            for k, v in scada_record.items()
            if k in ["trading_interval", "generated"]
        }
        for scada_record in scada
    ]

    data_grouped = {}

    for key, v in groupby(data, itemgetter("trading_interval")):
        if key not in data_grouped:
            data_grouped[key] = 0.0

        # @TODO abstract this
        total = sum(
            [
                i["generated"]
                for i in list(v)
                if type(i["generated"]) in [int, float, Decimal]
            ]
        )

        if total:
            total = float(total)
            data_grouped[key] = round(total, 2)

    history = OpennemDataHistory(
        start=start.astimezone(network_timezone),
        last=end.astimezone(network_timezone),
        interval=interval.interval_human,
        data=list(data_grouped.values()),
    )

    data = OpennemData(
        network=network.code,
        data_type="power",
        units="MW",
        code=code,
        history=history,
    )

    return data


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
