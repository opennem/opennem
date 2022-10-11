from datetime import datetime

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


def test_export_power_envelope() -> None:
    """Test the power return envelope"""
    power_set = FIXTURE_SET["NSW1"].power

    # check version
    assert hasattr(power_set, "version"), "Has a version attribute"
    assert power_set.version is not None, "Has a version value"
    assert isinstance(power_set.version, str), "Version is a string"

    # check type
    assert hasattr(power_set, "type"), "Has a type attribute"
    assert power_set.type is not None, "Has a type value"
    assert isinstance(power_set.type, str), "type is a string"
    assert power_set.type == "power", "type is power"

    # check network
    assert hasattr(power_set, "network"), "Has a network attribute"
    assert power_set.network is not None, "Has a network value"
    assert isinstance(power_set.network, str), "network is a string"
    assert power_set.network.lower() == "nem", "network is nem"

    # check created_at
    assert hasattr(power_set, "created_at"), "Has a created_at attribute"
    assert power_set.created_at is not None, "Has a created_at value"
    assert isinstance(power_set.created_at, str), "created_at is a str"
    assert isinstance(datetime.fromisoformat(power_set.created_at), datetime), "created_at is a datetime"


def test_export_power_fueltech_attributes() -> None:
    """Test the fueltech attributes"""
    power_set = FIXTURE_SET["NSW1"].power

    all_fueltech_ids = [i.id for i in power_set.data if i.id and "fueltech_id" in i.id]

    for series_id in all_fueltech_ids:
        series_data = power_set.get_id(series_id)
        assert hasattr(series_data, "fueltech_id"), "Has the fueltech_id attribute"
        assert hasattr(series_data, "code"), "Has a code attribute"
