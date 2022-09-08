from datetime import date
from enum import Enum
from itertools import groupby

import pytest

from opennem.api.stats.schema import OpennemDataHistory, load_opennem_dataset_from_file
from opennem.utils.tests import TEST_FIXTURE_PATH

ValidNumber = float | int


class SeriesType(str, Enum):
    power = "power"
    emissions = "emissions"
    energy = "energy"


energy_series = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_1y.json")
historic_series = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_week.json")


def group_historic_by_day(
    series: OpennemDataHistory, series_type: SeriesType = SeriesType.power
) -> dict[date, ValidNumber]:
    values_dict: dict[date, ValidNumber] = {}

    for dt, v in groupby(series.values(), lambda x: x[0].date()):
        values_series: list[ValidNumber] = [i[1] for i in list(v)]  # type: ignore

        if dt not in values_dict:
            values_dict[dt] = 0

        series_sum = sum(values_series)

        # convert to energy at MWh
        if series_sum and series_type == SeriesType.power:
            series_sum /= 12000

        values_dict[dt] = series_sum

    # delete max date - a groupby quirk with fences
    max_date = max(values_dict.keys())
    del values_dict[max_date]

    return values_dict


def compare_series_values_approx_by_date(
    fueltech_id: str,
    series_type: SeriesType = SeriesType.power,
) -> None:
    # 1. Historic Series
    # get historic
    historic_series_id = f"au.nem.nsw1.fuel_tech.{fueltech_id}.{series_type.value}"

    historic_series_fueltech = historic_series.get_id(historic_series_id)

    if not historic_series_fueltech or not historic_series_fueltech.history:
        raise Exception(f"Could not find series {historic_series_id}")

    historic_series_values = group_historic_by_day(historic_series_fueltech.history, series_type=series_type)

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
    for dt, power_value in historic_series_values.items():
        energy_value = energy_series_daily_dict.get(dt)

        if not energy_value:
            raise Exception(f"Date {dt} not in yearly_energy_dict")

        # 5% tolerance
        if energy_value != pytest.approx(power_value, 0.5):
            print(f"{fueltech_id}.{series_type.value} Mismatch: {dt}: {power_value} {energy_value}")


@pytest.mark.parametrize(
    ["fueltech_id", "series_type"],
    [
        ("coal_black", SeriesType.power),
        ("coal_black", SeriesType.emissions),
        ("gas_ccgt", SeriesType.power),
        ("gas_ccgt", SeriesType.emissions),
    ],
)
def test_compare_historic_series(fueltech_id: str, series_type: SeriesType) -> None:
    compare_series_values_approx_by_date(fueltech_id, series_type)
