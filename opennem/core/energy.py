# pylint: disable=no-self-argument
"""
OpenNEM Energy Tools

Uses an average in 30 minute buckets

@TODO variable bucket sizes

"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd
from pytz import FixedOffset

from opennem.schema.core import BaseConfig

logger = logging.getLogger("opennem.compat.energy")


class ScadaResultCompat(BaseConfig):
    interval: datetime
    code: Optional[str]
    generated: Union[float, int, None]


def _trapezium_integration_variable(d_ti: pd.Series) -> float:
    """Gapfill version of trap int - will fill out"""
    # Clear no numbers
    d_ti = d_ti.dropna()

    # Fall back on average but warn to check data
    if d_ti.count() <= 3:
        d_sum = d_ti.sum()

        if d_sum == 0:
            return 0

        if d_ti.count() == 0:
            return 0

        return 0.5 * d_sum / d_ti.count()

    bucket_middle = d_ti.count() - 2

    bucket_middle_weights = [1] + [2] * bucket_middle + [1]

    weights = d_ti.values * bucket_middle_weights

    weights_sum = weights.sum()

    bucket_energy = 0.5 * weights_sum / ((d_ti.count() - 1) * 2)

    return bucket_energy


def _trapezium_integration(d_ti: pd.Series) -> Optional[float]:
    """ Energy for a 30 minute bucket """
    # Clear no numbers
    d_ti = d_ti.dropna()

    # Fall back on average but warn to check data
    if d_ti.count() != 7:
        logger.warn("Series {} has gaps".format(d_ti))
        return _trapezium_integration_variable(d_ti)

    weights = d_ti.values * [1, 2, 2, 2, 2, 2, 1]

    weights_sum = weights.sum()

    bucket_energy = 0.5 * weights_sum / 12

    return bucket_energy


def energy_sum(gen_series: List[Dict]) -> pd.DataFrame:
    """Takes the energy sum for a series of raw duid intervals
    and returns a fresh dataframe to be imported"""
    df = pd.DataFrame(
        gen_series,
        columns=[
            "trading_interval",
            "facility_code",
            "network_id",
            "eoi_quantity",
        ],
    )

    # Clean up types
    df.trading_interval = pd.to_datetime(df.trading_interval)
    df.eoi_quantity = pd.to_numeric(df.eoi_quantity)

    # Index by datetime
    df = df.set_index(df.trading_interval)

    # Multigroup by datetime and facility code
    df = df.groupby([pd.Grouper(freq="30min", offset="5m"), "facility_code"]).eoi_quantity.apply(
        _trapezium_integration
    )

    # Reset back to a simple frame
    df = df.reset_index()

    # Shift back 5 minutes to even up into 30 minute bkocks
    df.trading_interval = df.trading_interval - pd.Timedelta(minutes=5)

    # Add back the timezone for NEM
    # We use a fixed offset so need to loop
    df.trading_interval = df.apply(
        lambda x: pd.Timestamp(x.trading_interval, tz=FixedOffset(600)), axis=1
    )

    df["network_id"] = "NEM"

    # filter out empties
    df = df[pd.isnull(df.eoi_quantity) == False]

    return df
