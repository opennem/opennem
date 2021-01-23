import pytest

from opennem.core.fueltechs import map_v2_fueltech, map_v3_fueltech


@pytest.mark.parametrize(
    ["fueltech", "fueltech_expected"],
    [
        ("black_coal", "coal_black"),
        ("brown_coal", "coal_brown"),
        ("none", "none"),
        ("wind", "wind"),
        ("solar", "solar_utility"),
        ("rooftop_solar", "solar_rooftop"),
    ],
)
def test_fueltech_map_v2(fueltech: str, fueltech_expected: str) -> None:
    fueltech_mapped = map_v2_fueltech(fueltech)
    assert fueltech_mapped == fueltech_expected


@pytest.mark.parametrize(
    ["fueltech", "fueltech_expected"],
    [
        ("coal_black", "black_coal"),
        ("coal_brown", "brown_coal"),
        ("none", "none"),
        ("wind", "wind"),
        ("solar_utility", "solar"),
        ("solar_rooftop", "rooftop_solar"),
    ],
)
def test_fueltech_map_v3(fueltech: str, fueltech_expected: str) -> None:
    fueltech_mapped = map_v3_fueltech(fueltech)
    assert fueltech_mapped == fueltech_expected
