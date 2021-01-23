import pytest

from opennem.core.fueltechs import map_v2_fueltech


@pytest.mark.parametrize(
    ["fueltech", "fueltech_expected"],
    [
        ("black_coal", "coal_black"),
        ("brown_coal", "coal_brown"),
        ("none", "none"),
        ("wind", "wind"),
        ("solar", "solar_utility"),
    ],
)
def test_fueltech_map_v2(fueltech: str, fueltech_expected: str) -> None:
    fueltech_mapped = map_v2_fueltech(fueltech)
    assert fueltech_mapped == fueltech_expected
