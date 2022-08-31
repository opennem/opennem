from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from datedelta import datedelta

from opennem.api.stats.schema import load_opennem_dataset_from_file
from opennem.core.validators.data import validate_data_outputs
from opennem.utils.interval import get_human_interval
from opennem.utils.numbers import generate_random_number_series
from opennem.utils.tests import TEST_FIXTURE_PATH

ValidNumber = float | int | None | Decimal


@pytest.mark.parametrize(
    ["series", "interval_size", "start_date", "end_date", "expected"],
    [
        (
            generate_random_number_series(30),
            get_human_interval("1d"),
            datetime(2019, 1, 1),
            datetime(2019, 1, 31),
            True,
        ),
        (
            generate_random_number_series(12),
            get_human_interval("5m"),
            datetime.fromisoformat("2020-01-01T00:00:00+10:00"),
            datetime.fromisoformat("2020-01-01T01:00:00+10:00"),
            True,
        ),
    ],
)
def test_validate_data_outputs(
    series: list[ValidNumber],
    interval_size: timedelta | datedelta,
    start_date: datetime,
    end_date: datetime,
    expected: bool,
) -> None:
    subject_value = validate_data_outputs(
        series,
        interval_size=interval_size,
        start_date=start_date,
        end_date=end_date,
    )
    assert subject_value == expected, "This test should pass"


power_series = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_7d.json")


@pytest.mark.parametrize(
    ["series_id", "expected_validation"],
    [
        ("au.nem.nsw1.fuel_tech.coal_black.power", True),
        ("au.nem.nsw1.fuel_tech.coal_black.power", True),
        ("au.nem.nsw1.fuel_tech.wind.power", True),
        ("nem.nsw1.au.price", True),
        ("au.nem.nsw1.fuel_tech.solar_rooftop.power", True),
        ("nem.nsw1.demand.demand", True),
    ],
)
def _test_validate_power_series(series_id: str, expected_validation: bool) -> None:
    """Test the power series from the local fixture"""
    test_case = power_series.get_id(series_id)

    # @TODO error on this test case
    if not test_case:
        return None

    test_case_history = test_case.history

    series_is_validated = validate_data_outputs(
        test_case_history.data,
        test_case_history.get_interval(),
        test_case_history.start,
        test_case_history.last,
    )

    assert series_is_validated == expected_validation

    return None


energy_series = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_1y.json")


@pytest.mark.parametrize(
    ["series_id", "expected_validation"],
    [
        ("au.nem.nsw1.fuel_tech.wind.energy", True),
        ("au.nem.nsw1.fuel_tech.wind.market_value", True),
        ("au.nem.nsw1.fuel_tech.coal_black.emissions", True),
        ("au.nem.nsw1.demand.energy", True),
        ("au.nem.nsw1.demand.market_value", True),
        ("au.nem.nsw1.fuel_tech.imports.energy", True),
        ("au.nem.nsw1.fuel_tech.exports.emissions", True),
        ("au.nem.nsw1.fuel_tech.imports.market_value", True),
        ("au.nem.nsw1.temperature_mean", True),
        ("au.nem.nsw1.temperature_min", True),
    ],
)
def _test_validate_energy_series(series_id: str, expected_validation: bool) -> None:
    """Test the energy series from the local fixture"""

    test_case = energy_series.get_id(series_id)

    # @TODO error on this test case
    if not test_case:
        return None

    test_case_history = test_case.history

    series_is_validated = validate_data_outputs(
        test_case_history.data,
        test_case_history.get_interval(),
        test_case_history.start,
        test_case_history.last,
    )

    assert series_is_validated == True

    return None
