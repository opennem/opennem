"""
Tests for the per-interval export series in opennem.exporter.historic


"""
from datetime import date
from itertools import groupby

import pytest

from opennem.api.stats.schema import OpennemDataHistory, OpennemDataSet
from tests.conftest import OpennemTestException

from .utils import FIXTURE_SET, SeriesType, ValidNumber


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

        if series_type == SeriesType.power and is_flow:
            series_sum *= 12
            series_sum /= 1000

        if series_type == SeriesType.emissions and is_flow:
            series_sum *= 12

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
        raise OpennemTestException(f"Could not find series {historic_series_id}")

    is_flow = fueltech_id in {"imports", "exports"}

    historic_series_values = group_historic_by_day(historic_series_fueltech.history, series_type=series_type, is_flow=is_flow)

    # 2. Energy Series
    # grouped by day already
    if series_type == SeriesType.power:
        series_type = SeriesType.energy

    energy_series_id = f"au.nem.nsw1.fuel_tech.{fueltech_id}.{series_type.value}"
    energy_series_fueltech = energy_series.get_id(energy_series_id)

    if not energy_series_fueltech:
        raise OpennemTestException(f"Could not find energy series with id {energy_series_id}")

    energy_series_values = energy_series_fueltech.history.values()

    # group by date
    energy_series_daily_dict = {i[0].date(): i[1] for i in energy_series_values}

    # compare dates
    for dt, historic_value in historic_series_values.items():
        energy_value = energy_series_daily_dict.get(dt)

        if not energy_value:
            raise OpennemTestException(f"Date {dt} not in yearly_energy_dict")

        # 5% tolerance
        # required as the series won't precisely match as naive energy sum per
        # interval vs full per-hour AUC-energy sum
        if energy_value != pytest.approx(historic_value, 0.5):
            raise OpennemTestException(f"{fueltech_id}.{series_type.value} Mismatch: {dt}: {historic_value} {energy_value}")


@pytest.mark.parametrize(
    ["region_id", "fueltech_id", "series_type"],
    [
        ("NSW1", "coal_black", SeriesType.power),
        ("NSW1", "coal_black", SeriesType.emissions),
        ("NSW1", "gas_ccgt", SeriesType.power),
        ("NSW1", "gas_ccgt", SeriesType.emissions),
        ("NSW1", "exports", SeriesType.power),
        ("NSW1", "exports", SeriesType.emissions),
        ("NSW1", "imports", SeriesType.power),
        ("NSW1", "imports", SeriesType.emissions),
    ],
)
def test_compare_nem_weekly_series(region_id: str, fueltech_id: str, series_type: SeriesType) -> None:
    """Tests the values of the historic series against the daily energy series"""
    weekly_series = FIXTURE_SET[region_id].weekly
    daily_series = FIXTURE_SET[region_id].daily

    compare_series_values_approx_by_date(
        fueltech_id, historic_series=weekly_series, energy_series=daily_series, series_type=series_type
    )


@pytest.mark.parametrize(
    ["region_id", "series_type", "fueltech_id"],
    [
        ("NSW1", SeriesType.power, "coal_black"),
        ("NSW1", SeriesType.power, "wind"),
        ("NSW1", SeriesType.emissions, "coal_black"),
        ("NSW1", SeriesType.power, "imports"),
        ("NSW1", SeriesType.emissions, "imports"),
        ("NSW1", SeriesType.power, "exports"),
        ("NSW1", SeriesType.emissions, "exports"),
        ("NSW1", SeriesType.power, "imports"),
        ("NSW1", SeriesType.emissions, "imports"),
        ("NSW1", SeriesType.demand, None),
        ("NSW1", SeriesType.temperature, None),
        ("NSW1", SeriesType.price, None),
    ],
)
def test_weekly_contains_all_ids(region_id: str, series_type: SeriesType, fueltech_id: str | None) -> None:
    series_id_components = ["au.nem.nsw1"]

    if fueltech_id:
        series_id_components.extend(("fuel_tech", fueltech_id))

    series_id_components.append(series_type.value)

    series_id = ".".join(series_id_components)

    series_set = FIXTURE_SET[region_id].weekly.get_id(series_id)

    if not series_set:
        raise OpennemTestException(f"Could not find id: {series_id}")


# debug entry point for unit tests
if __name__ == "__main__":
    try:
        compare_series_values_approx_by_date(
            "exports",
            historic_series=FIXTURE_SET["NSW1"].weekly,
            energy_series=FIXTURE_SET["NSW1"].daily,
            series_type=SeriesType.power,
        )
    except Exception as e:
        print(e)
