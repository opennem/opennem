"""
OpenNEM v2 compatible version of energy sums

Uses an average in 30 minute buckets
"""
from datetime import date, datetime, timedelta, tzinfo
from typing import Dict, Generator, List, Optional, Tuple, Union

import pandas as pd
from pytz import FixedOffset

from opennem.schema.core import BaseConfig


class ScadaResultCompat(BaseConfig):
    interval: datetime
    code: Optional[str]
    generated: Union[float, int, None]


def __trading_energy_generator(
    df: pd.DataFrame, duid: str, sel_date: datetime
) -> Generator[Tuple[date, str, str, str, float], None, None]:
    df.sort_index(inplace=True)
    t_start = datetime(sel_date.year, sel_date.month, sel_date.day, 0, 5)

    # 48 trading intervals in the day
    # (could be better with groupby function)
    for TI in range(48):
        # t_i initial timestamp of trading_interval, t_f = final timestamp of trading interval
        t_i = t_start + timedelta(0, 1800 * TI)
        t_f = t_start + timedelta(0, 1800 * (TI + 1))

        d_ti = df[(df.index >= t_i) & (df.index <= t_f) & (df.facility_code == duid)]

        if d_ti.empty or d_ti.size < 7:
            continue

        yield d_ti.index[-2].replace(tzinfo=FixedOffset(600)), duid, d_ti.network_id.unique()[
            0
        ], d_ti.network_region.unique()[0], __trapezium_integration(d_ti.generated)


def __trapezium_integration(d_ti: pd.Series) -> float:
    if d_ti.count() < 7:
        return 0

    weights = d_ti.values * [1, 2, 2, 2, 2, 2, 1]

    weights_sum = weights.sum()

    bucket_energy = 0.5 * weights_sum / 12

    return bucket_energy


def energy_sum_compat(gen_series: List[Dict]) -> List[Dict]:
    df = pd.DataFrame(
        gen_series,
        columns=[
            "trading_interval",
            "facility_code",
            "network_id",
            "network_region",
            "generated",
        ],
    )
    df.trading_interval = pd.to_datetime(df.trading_interval)
    df.generated = pd.to_numeric(df.generated)
    df = df.set_index(df.trading_interval)

    sel_date = df.index.min().date()
    max_date = df.index.max().date()

    return_list = []

    for duid in list(df.facility_code.unique()):
        sel_date = df.trading_interval.min().date()

        while sel_date <= max_date:
            next_frame = [d for d in __trading_energy_generator(df, duid, sel_date)]
            return_list += next_frame
            sel_date = sel_date + timedelta(days=1)

    return_frame = pd.DataFrame(
        return_list,
        columns=[
            "trading_interval",
            "facility_code",
            "network_id",
            "network_region",
            "eoi_quantity",
        ],
        # index=["trading_interval"],
    )

    return_frame = return_frame.set_index(return_frame.trading_interval)
    del return_frame["trading_interval"]

    return return_frame.to_csv()
