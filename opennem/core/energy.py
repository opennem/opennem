# pylint: disable=no-self-argument
"""
OpenNEM Energy Tools

Uses an average in 30 minute buckets

@TODO variable bucket sizes

"""
import logging
from collections.abc import Generator
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM, NetworkSchema

logger = logging.getLogger("opennem.compat.energy")


class ScadaResultCompat(BaseConfig):
    interval: datetime
    code: str | None
    generated: float | int | None


def __trapezium_integration(d_ti: pd.Series, power_field: str = "MWH_READING") -> pd.Series:
    return 0.5 * (d_ti[power_field] * [1, 2, 2, 2, 2, 2, 1]).sum() / 12


def __trading_energy_generator(df: pd.DataFrame, date: date, duid_id: str, power_field: str = "generated") -> pd.DataFrame:
    return_cols = []

    t_start = datetime(date.year, date.month, date.day, 0, 5, tzinfo=NetworkNEM.get_fixed_offset())

    # 48 trading intervals in the day
    # (could be better with groupby function)
    for TI in range(48):
        # t_i initial timestamp of trading_interval, t_f = final timestamp of trading interval
        t_i = t_start + timedelta(0, 1800 * TI)
        t_f = t_start + timedelta(0, 1800 * (TI + 1))

        _query = f"'{t_i}' <= trading_interval <= '{t_f}' and facility_code == '{duid_id}'"

        d_ti = df.query(_query)

        energy_value = None
        trading_interval = None

        # rooftop 30m intervals - AEMO rooftop is going to go in a separate network
        # so this won't be required
        if (d_ti.fueltech_id.all() == "solar_rooftop") and (d_ti[power_field].count() == 1):
            energy_value = d_ti[power_field].sum() / 2
            # ooofff - this delta comes back off as part of NEM offset
            trading_interval = d_ti.index[0] + timedelta(minutes=5)
        # interpolate if it isn't padded out
        elif d_ti[power_field].count() != 7:
            index_interpolated = pd.date_range(start=t_i, end=t_f, freq="5min", tz=NetworkNEM.get_timezone())

            d_ti = d_ti.reset_index()
            d_ti = d_ti.set_index("trading_interval")
            d_ti = d_ti.reindex(index_interpolated)
            d_ti["facility_code"] = duid_id
            d_ti[power_field] = d_ti[power_field].replace(np.NaN, 0)

            if d_ti[power_field].count() != 7:
                logger.warning("Interpolated frame didn't match generated count")

        try:
            if d_ti.fueltech_id.all() != "solar_rooftop":
                energy_value = __trapezium_integration(d_ti, power_field)
                trading_interval = d_ti.index[-2]
        except ValueError as e:
            logger.error(f"Error with {duid_id} at {t_i} {t_f}: {e}")

        if not d_ti.index.empty:
            return_cols.append(
                {
                    "trading_interval": trading_interval,
                    "network_id": "NEM",
                    "facility_code": duid_id,
                    "eoi_quantity": energy_value,
                }
            )

    return return_cols


def __trading_energy_generator_hour(
    df: pd.DataFrame, hour: datetime, duid_id: str, power_field: str = "generated"
) -> pd.DataFrame:
    return_cols = []

    t_start = hour.replace(minute=5)

    for TI in range(2):
        t_i = t_start + timedelta(0, 1800 * TI)
        t_f = t_start + timedelta(0, 1800 * (TI + 1))

        _query = f"'{t_i}' <= trading_interval <= '{t_f}' and facility_code == '{duid_id}'"

        d_ti = df.query(_query)

        energy_value = None
        trading_interval = None

        # rooftop 30m intervals - AEMO rooftop is going to go in a separate network
        # so this won't be required
        if (d_ti.fueltech_id.all() == "solar_rooftop") and (d_ti[power_field].count() == 1):
            energy_value = d_ti[power_field].sum() / 2
            # ooofff - this delta comes back off as part of NEM offset
            trading_interval = d_ti.index[0] + timedelta(minutes=5)
        # interpolate if it isn't padded out
        elif d_ti[power_field].count() != 7:
            index_interpolated = pd.date_range(start=t_i, end=t_f, freq="5min", tz=NetworkNEM.get_timezone())

            d_ti = d_ti.reset_index()
            d_ti = d_ti.set_index("trading_interval")
            d_ti = d_ti.reindex(index_interpolated)
            d_ti["facility_code"] = duid_id
            d_ti[power_field] = d_ti[power_field].replace(np.NaN, 0)

            if d_ti[power_field].count() != 7:
                logger.warning("Interpolated frame didn't match generated count")

        try:
            if d_ti.fueltech_id.all() != "solar_rooftop":
                energy_value = __trapezium_integration(d_ti, power_field)
                trading_interval = d_ti.index[-2]
        except ValueError as e:
            logger.error(f"Error with {duid_id} at {t_i} {t_f}: {e}")

        if not d_ti.index.empty:
            return_cols.append(
                {
                    "trading_interval": trading_interval,
                    "network_id": "NEM",
                    "facility_code": duid_id,
                    "eoi_quantity": energy_value,
                }
            )

    return return_cols


def get_day_range(df: pd.DataFrame) -> Generator[date, None, None]:
    """Get the day range for a dataframe"""
    min_date = (df.index.min() + timedelta(days=1)).date()
    max_date = (df.index.max() - timedelta(days=1)).date()

    cur_day = min_date

    while cur_day <= max_date:
        yield cur_day
        cur_day += timedelta(days=1)


def get_hour_range(df: pd.DataFrame) -> Generator[datetime, None, None]:
    """Get the hour range for a dataframe"""
    min_date = df.index.min()
    max_date = df.index.max()

    logger.debug(f"Datafram date range is {min_date} -> {max_date}")

    cur_hour = min_date

    while cur_hour <= max_date - timedelta(hours=1):
        yield cur_hour
        cur_hour += timedelta(hours=1)


def _energy_aggregate_compat(df: pd.DataFrame) -> pd.DataFrame:
    """v2 version of energy_sum for compat"""
    energy_genrecs = []

    days = list(get_day_range(df))

    if len(days) == 0:
        logger.error("Got no days from day range")

    for day in days:
        for duid in sorted(df.facility_code.unique()):
            energy_genrecs += [d for d in __trading_energy_generator(df, day, duid)]

    df = pd.DataFrame(energy_genrecs, columns=["trading_interval", "network_id", "facility_code", "eoi_quantity"])

    return df


def _energy_aggregate_hours(df: pd.DataFrame) -> pd.DataFrame:
    """v3 version of energy_sum for compat"""
    energy_genrecs = []

    hours = list(get_hour_range(df))

    for hour in hours:
        logger.info(f"Running for hour: {hour}")
        for duid in sorted(df.facility_code.unique()):
            energy_genrecs += [d for d in __trading_energy_generator_hour(df, hour, duid)]

    df = pd.DataFrame(energy_genrecs, columns=["trading_interval", "network_id", "facility_code", "eoi_quantity"])

    return df


def _trapezium_integration_variable(d_ti: pd.Series) -> float | None:
    """Gapfill version of trap int - will fill out"""
    # Clear no numbers
    d_ti = d_ti.dropna()

    if d_ti.count() == 0:
        return None

    # One entry
    if d_ti.count() == 1:
        return d_ti[0] * 0.5

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


def _energy_aggregate(df: pd.DataFrame, power_column: str = "generated", zero_fill: bool = False) -> pd.DataFrame:
    """v3 version of energy aggregate for energy_sum - iterates over time bucekts with edges"""
    in_cap = {}
    capture: dict[str, Any] = {}
    values = []
    dt: datetime | None = None
    reading_stops: list[int] = [0, 30]

    for index, value in df.iterrows():
        i, network_id, duid = index

        if duid not in capture:
            capture[duid] = []
            in_cap[duid] = True

        if in_cap[duid]:
            capture[duid].append(value[power_column])

            if dt:
                energy = _trapezium_integration_variable(pd.Series(capture[duid]))
                values.append((dt, network_id, duid, energy))

            in_cap[duid] = False
            capture[duid] = []

        if i.minute in reading_stops:
            dt = i
            capture[duid].append(value[power_column])
            in_cap[duid] = True

        else:
            capture[duid].append(value[power_column])

    return pd.DataFrame(values, columns=["trading_interval", "network_id", "facility_code", "eoi_quantity"])


def shape_energy_dataframe(gen_series: list[dict], network: NetworkSchema = NetworkNEM) -> pd.DataFrame:
    """Shapes a list of dicts into a dataframe for energy_sum"""
    df = pd.DataFrame(
        gen_series,
        columns=[
            "trading_interval",
            "facility_code",
            "network_id",
            "fueltech_id",
            "generated",
        ],
    )

    # Clean up types
    df.trading_interval = pd.to_datetime(df.trading_interval)
    df.generated = pd.to_numeric(df.generated)

    # timezone from network
    df.trading_interval = df.apply(lambda x: pd.Timestamp(x.trading_interval, tz=network.get_fixed_offset()), axis=1)

    return df


def energy_sum(
    df: pd.DataFrame,
    network: NetworkSchema,
    power_column: str = "generated",
    filter_no_energy_values: bool = True,
    hours: bool = True,
) -> pd.DataFrame:
    """Takes the energy sum for a series of raw duid intervals
    and returns a fresh dataframe to be imported"""

    # These are the networks that run through the compat func
    COMPAT_NETWORKS = [NetworkNEM]

    if network in COMPAT_NETWORKS:
        df = df.set_index(["trading_interval"])
        if hours:
            if len(list(get_hour_range(df))) == 0:
                logger.warning(f"energy_sum error for network {network.code}: Got no hours from hour range")

            df = _energy_aggregate_hours(df)
        else:
            df = _energy_aggregate(df)

    # Shortcuts - @NOTE this is a v2 compat feature
    # since it takes these averages - remove for full
    # sum
    elif network.interval_size == 30:
        df["eoi_quantity"] = df.generated / 2
        df = df.drop("generated", axis=1)

    elif network.interval_size == 15:
        df["eoi_quantity"] = df.generated / 4
        df = df.drop("generated", axis=1)

    else:
        # Index by datetime
        df = df.set_index(["trading_interval", "network_id", "facility_code"])

        # Multigroup by datetime and facility code
        df = _energy_aggregate(df, power_column=power_column)

    # Reset back to a simple frame
    df = df.reset_index()

    # Shift back if required by network
    if network.interval_shift:
        df.trading_interval = df.trading_interval - pd.Timedelta(minutes=network.interval_shift)

    # filter out empties
    if filter_no_energy_values:
        df = df[pd.isnull(df.eoi_quantity) == False]  # noqa: E712

    return df
