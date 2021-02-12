import json
from pathlib import Path
from typing import List

import pytest

from opennem.core.energy import Point, energy_sum, trapozedoid

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "energy"

MINUTES_IN_DAY = 1440


def load_energy_fixture(fixture_name: str) -> List:
    fixture_file_path = FIXTURE_PATH / fixture_name

    if not fixture_file_path.is_file():
        raise Exception("Fixture {} not found".format(fixture_name))

    fixture_envelope = None

    with fixture_file_path.open() as fh:
        fixture_envelope = json.load(fh)

    return fixture_envelope


@pytest.mark.parametrize(
    ["p1", "p2", "expected_area"],
    [
        (Point(x=1, y=0), Point(x=2, y=5), 7.5),
        (Point(x=2, y=0), Point(x=1, y=5), 7.5),
        (Point(x=10946.91, y=0), Point(x=10777.92, y=5), 54312.075),
    ],
)
def test_trapezoid_cal(p1: Point, p2: Point, expected_area: float) -> None:
    calculated_area = trapozedoid(p1, p2)

    assert calculated_area == expected_area, "Area calculation is expected"


@pytest.mark.parametrize(
    ["series", "expected"],
    [
        ([1, 2], 0.75),
        ([1, 1, 1], 1 / 3 * 2),
        ([1.0, 2.0, 1.0], 1),
        ([2.0, -1.0, 2.0], 1 / 3),
        ([1, None, 1], 1 / 3),
    ],
)
def test_energy_sum(series: List, expected: float) -> None:
    energy_value = energy_sum(series, 60)

    assert energy_value == expected, "Got expected energy value"


@pytest.mark.parametrize(
    ["fixture_name", "actual_value", "p_variation", "test_exact"],
    [
        ("coal_black_1_day.json", 248.88 * 1000, 0.2, False),
        ("23_oct_rooftop.json", 9059.75, 0.2, True),
        ("battery_charging_1_day.json", -0.21 * 1000, 0.2, False),
        ("23_oct_wem_gas.json", 10265.32, 0.2, True),
    ],
)
def test_energy_sum_fixtures(
    fixture_name: str, actual_value: float, p_variation: float, test_exact: bool
) -> None:
    fixture = load_energy_fixture(fixture_name)

    energy_value = energy_sum(fixture, MINUTES_IN_DAY)
    variation = (energy_value - actual_value) / actual_value

    if p_variation:
        assert variation < 0.2, "Variation in rooftop value is less than 0.2"

    if test_exact:
        assert actual_value == energy_value, "Values are exact"
