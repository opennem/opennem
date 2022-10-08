import pytest

from .utils import FIXTURE_SET


@pytest.mark.parametrize(
    ["network_region_code", "fueltech_ids"],
    [
        ("NSW1", ["coal_black", "wind", "hydro", "gas_ccgt", "solar_utility"]),
        ("VIC1", ["coal_brown", "solar_utility", "wind"]),
        ("SA1", ["solar_utility", "wind"]),
        ("QLD1", ["coal_black", "wind", "hydro", "solar_utility"]),
        ("TAS1", ["hydro", "wind", "gas_ocgt"]),
    ],
)
def test_export_power_ids(network_region_code: str, fueltech_ids: list[str]) -> None:
    """Tests the values of the power series and ensure it has all required ids"""

    power_set = FIXTURE_SET[network_region_code].power

    for fueltech_id in fueltech_ids:
        assert power_set.get_id(f"au.nem.{network_region_code.lower()}.fuel_tech.{fueltech_id}.power") is not None

    # test that it has rooftop
    assert power_set.get_id(f"au.nem.{network_region_code.lower()}.fuel_tech.solar_rooftop.power") is not None

    # demand and price
    assert power_set.get_id(f"au.nem.{network_region_code.lower()}.demand") is not None
    assert power_set.get_id(f"au.nem.{network_region_code.lower()}.price") is not None
    assert power_set.get_id(f"au.nem.{network_region_code.lower()}.temperature") is not None


def test_export_power_fueltech_attributes() -> None:
    """Test the fueltech attributes"""
    power_set = FIXTURE_SET["NSW1"].power

    all_ids = [i.id for i in power_set.data if i.id and "fueltech_id" in i.id]

    for series_id in all_ids:
        series_data = power_set.get_id(series_id)
        assert hasattr(series_data, "fueltech_id")
