"""
Tests for the per-interval export series in opennem.exporter.historic


"""
from datetime import date
from enum import Enum
from itertools import groupby

import pytest

from opennem.api.stats.schema import (
    OpennemDataHistory,
    OpennemDataSet,
    load_opennem_dataset_from_file,
    load_opennem_dataset_from_url,
)
from opennem.utils.security import get_random_string
from opennem.utils.tests import TEST_FIXTURE_PATH

ValidNumber = float | int


class SeriesType(str, Enum):
    power = "power"
    emissions = "emissions"
    energy = "energy"
    demand = "demand"
    price = "price"
    temperature = "temperature"


energy_series = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_1y.json")
nem_nsw1_week_local = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_week.json")
nem_nsw1_week_live = load_opennem_dataset_from_url(
    f"https://data.dev.opennem.org.au/v3/stats/historic/weekly/NEM/NSW1/year/2022/week/36.json?q={get_random_string()}"
)


def group_historic_by_day(
    series: OpennemDataHistory,
    series_type: SeriesType = SeriesType.power,
    is_flow: bool = False,
) -> dict[date, ValidNumber]:
    values_dict: dict[date, ValidNumber] = {}

    for dt, v in groupby(series.values(), lambda x: x[0].date()):
        values_series: list[ValidNumber] = [i[1] for i in list(v)]  # type: ignore

        if dt not in values_dict:
            values_dict[dt] = 0

        series_sum = sum(values_series)

        if not series_sum:
            continue

        # convert to energy at MWh
        if series_type == SeriesType.power and not is_flow:
            series_sum /= 12000

        values_dict[dt] = series_sum

    # delete max date - a groupby quirk with fences
    max_date = max(values_dict.keys())
    del values_dict[max_date]

    return values_dict


def compare_series_values_approx_by_date(
    fueltech_id: str,
    historic_series: OpennemDataSet,
    energy_series: OpennemDataSet,
    series_type: SeriesType = SeriesType.power,
) -> None:
    # 1. Historic Series
    # get historic
    historic_series_id = f"au.nem.nsw1.fuel_tech.{fueltech_id}.{series_type.value}"

    historic_series_fueltech = historic_series.get_id(historic_series_id)

    if not historic_series_fueltech or not historic_series_fueltech.history:
        raise Exception(f"Could not find series {historic_series_id}")

    # if its a flow type we don't need to do the sum
    is_flow = False

    if fueltech_id in ["imports", "exports"]:
        is_flow = True

    historic_series_values = group_historic_by_day(
        historic_series_fueltech.history, series_type=series_type, is_flow=is_flow
    )

    # 2. Energy Series
    # grouped by day already
    if series_type == SeriesType.power:
        series_type = SeriesType.energy

    energy_series_id = f"au.nem.nsw1.fuel_tech.{fueltech_id}.{series_type.value}"
    energy_series_fueltech = energy_series.get_id(energy_series_id)

    if not energy_series_fueltech:
        raise Exception(f"Could not find energy series with id {energy_series_id}")

    energy_series_values = energy_series_fueltech.history.values()

    # group by date
    energy_series_daily_dict = {i[0].date(): i[1] for i in energy_series_values}

    # compare dates
    for dt, historic_value in historic_series_values.items():
        energy_value = energy_series_daily_dict.get(dt)

        if not energy_value:
            raise Exception(f"Date {dt} not in yearly_energy_dict")

        # 5% tolerance
        # required as the series won't precisely match as naive energy sum per
        # interval vs full per-hour AUC-energy sum
        if energy_value != pytest.approx(historic_value, 0.5):
            raise Exception(f"{fueltech_id}.{series_type.value} Mismatch: {dt}: {historic_value} {energy_value}")


@pytest.mark.parametrize(
    ["fueltech_id", "series_type"],
    [
        ("coal_black", SeriesType.power),
        ("coal_black", SeriesType.emissions),
        ("gas_ccgt", SeriesType.power),
        ("gas_ccgt", SeriesType.emissions),
        ("exports", SeriesType.power),
        ("exports", SeriesType.emissions),
        ("imports", SeriesType.power),
        ("imports", SeriesType.emissions),
    ],
)
def test_compare_historic_series(fueltech_id: str, series_type: SeriesType) -> None:
    """Tests the values of the historic series against the daily energy series"""
    compare_series_values_approx_by_date(
        fueltech_id, historic_series=nem_nsw1_week_live, energy_series=energy_series, series_type=series_type
    )


@pytest.mark.parametrize(
    ["series_type", "fueltech_id"],
    [
        (SeriesType.power, "coal_black"),
        (SeriesType.power, "wind"),
        (SeriesType.emissions, "coal_black"),
        (SeriesType.power, "imports"),
        (SeriesType.emissions, "imports"),
        (SeriesType.power, "exports"),
        (SeriesType.emissions, "exports"),
        (SeriesType.power, "imports"),
        (SeriesType.emissions, "imports"),
        (SeriesType.demand, None),
        (SeriesType.temperature, None),
        (SeriesType.price, None),
    ],
)
def test_historic_contains_all_ids(series_type: SeriesType, fueltech_id: str | None) -> None:
    series_id_components = ["au.nem.nsw1"]

    if fueltech_id:
        series_id_components.append("fuel_tech")
        series_id_components.append(fueltech_id)

    series_id_components.append(series_type.value)

    series_id = ".".join(series_id_components)

    series_set = nem_nsw1_week_live.get_id(series_id)

    if not series_set:
        raise Exception(f"Could not find id: {series_id}")


# debug entry point for unit tests
if __name__ == "__main__":
    try:
        compare_series_values_approx_by_date(
            "exports", historic_series=nem_nsw1_week_live, energy_series=energy_series, series_type=SeriesType.emissions
        )
    except Exception as e:
        print(e)
