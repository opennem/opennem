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


def test_energy_sum_coal_black() -> None:
    fixture = load_energy_fixture("coal_black_1_day.json")

    assert len(fixture) == 288, "Got correct fixture length"

    energy_value = energy_sum(fixture, MINUTES_IN_DAY)
    actual_value = 248.88 * 1000
    variation = (energy_value - actual_value) / actual_value

    assert variation < 0.2, "Variation in coal_black value is less than 0.2"


def test_energy_sum_rooftop() -> None:
    fixture = load_energy_fixture("23_oct_rooftop.json")

    energy_value = energy_sum(fixture, MINUTES_IN_DAY)
    actual_value = 9059.75
    variation = (energy_value - actual_value) / actual_value

    assert variation < 0.2, "Variation in rooftop value is less than 0.2"
    assert actual_value == energy_value, "Values are exact"
