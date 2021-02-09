#!/usr/bin/env python
import logging
from datetime import datetime, timedelta
from itertools import groupby

import pandas as pd

from opennem.api.export.map import StatType
from opennem.api.stats.schema import OpennemData, OpennemDataSet, ScadaDateRange
from opennem.core.compat.utils import translate_id_v2_to_v3
from opennem.db import get_database_engine
from opennem.diff.versions import get_network_regions, get_url_map
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM

logger = logging.getLogger("energy_diffs")


class ScadaResults(BaseConfig):
    trading_interval: datetime
    code: str
    generated: float


def __trading_energy_generator(df):
    df.sort_index(inplace=True)
    t_start = df.index.min()
    t_end = df.index.max()
    half_hour = timedelta(0, 1800)

    t_i = t_start
    t_f = t_start + half_hour

    # 48 trading intervals in the day
    # (could be better with groupby function)
    while t_f <= t_end:
        # t_i initial timestamp of trading_interval, t_f = final timestamp of trading interval
        t_i += half_hour
        t_f += half_hour

        for code in df.code.unique():
            d_ti = df[(df.index >= t_i) & (df.index <= t_f) & (df.code == code)]
            yield d_ti.index[-2], code, __trapezium_integration(d_ti.generated)


def __trapezium_integration(d_ti):
    if d_ti.count() < 7:
        return 0

    return 0.5 * (d_ti.values * [1, 2, 2, 2, 2, 2, 1]).sum() / 12


def get_v2_compat_data() -> OpennemDataSet:
    query = """
    select
        trading_interval at time zone 'AEST' as trading_interval,
        facility_code,
        generated
    from facility_scada
    where
        facility_code in ('LD01', 'LD02', 'LD03', 'LD04', 'BW01', 'BW02', 'BW03', 'BW04', 'MP1', 'ER01', 'ER02', 'ER03', 'ER04', 'MM3', 'MM4', 'MP2', 'REDBANK1', 'VP5', 'VP6', 'WW7', 'WW8')
        and trading_interval >= '2021-01-01 00:00:00+10'
    order by trading_interval asc;
    """

    engine = get_database_engine()

    with engine.connect() as c:
        logger.debug(query)
        res = list(c.execute(query))

    results = [ScadaResults(trading_interval=i[0], code=i[1], generated=i[2]).dict() for i in res]

    return results


def get_v2_compat():
    p = get_v2_compat_data()

    df = pd.DataFrame(p)
    df.trading_interval = pd.to_datetime(df.trading_interval)
    df = df.set_index("trading_interval")

    intervals = pd.DataFrame(
        [d for d in __trading_energy_generator(df)],
        columns=["trading_interval", "code", "energy"],
    )
    # intervals = intervals.set_index("trading_interval")
    intervals.to_csv("intervals.csv")

    dailies = intervals.to_dict("records")

    dailies_grouped = {}

    for day, values in groupby(dailies, key=lambda x: x["trading_interval"].date()):
        v = list(values)

        if day not in dailies_grouped:
            dailies_grouped[day] = 0.0

        for i in v:
            dailies_grouped[day] += i["energy"] / 1000

    return list(zip(dailies_grouped.keys(), dailies_grouped.values()))


import csv


def energy_diff() -> None:
    # get nsw1
    regions = get_network_regions(NetworkNEM, "NSW1")
    statsetmap = get_url_map(regions)

    # load urls
    [i.load_maps() for i in statsetmap]

    # filter it down to dailies
    energy_dailies = list(
        filter(lambda x: x.stat_type == StatType.energy and x.bucket_size == "daily", statsetmap)
    ).pop()

    if not energy_dailies.v2 or not energy_dailies.v3:
        raise Exception("error getting v2 or v3 data")

    # get coal_black
    fueltech_key = "nsw1.fuel_tech.black_coal.energy"

    v2 = energy_dailies.v2.get_id(fueltech_key)
    v3 = energy_dailies.v3.get_id(translate_id_v2_to_v3(fueltech_key))
    v2_computed = get_v2_compat()

    from pprint import pprint

    pprint(v2.history.values())

    print("---")

    pprint(v3.history.values())

    print("---")

    pprint(v2_computed)

    print("---")

    full_vals = []


if __name__ == "__main__":
    energy_diff()
