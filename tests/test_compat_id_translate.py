import pytest

from opennem.core.compat import translate_id_v3_to_v2


@pytest.mark.parametrize(
    ["id", "id_expected"],
    [
        ("nem.tas1.fuel_tech.coal_black.energy", "tas1.fuel_tech.black_coal.energy"),
        ("nem.tas1.fuel_tech.coal_black.power", "tas1.fuel_tech.black_coal.power"),
        ("nem.tas1.fuel_tech.wind.power", "tas1.fuel_tech.wind.power"),
        ("nem.tas1.price", "tas1.price"),
        ("nem.tas1.temperature.094029.temperature", "tas1.temperature"),
        ("nem.tas1.temperature.094029.temperature_mean", "tas1.temperature_mean"),
        ("nem.tas1.fuel_tech.gas_ocgt.market_value", "tas1.fuel_tech.gas_ocgt.market_value"),
        ("nem.tas1.fuel_tech.coal_black.market_value", "tas1.fuel_tech.black_coal.market_value"),
        ("nem.tas1.fuel_tech.solar_rooftop.energy", "tas1.fuel_tech.rooftop_solar.energy"),
        ("nem.tas1.fuel_tech.imports.emissions", "tas1.fuel_tech.imports.emissions"),
        ("nem.tas1.demand", "tas1.demand"),
    ],
)
def test_translate_id_v3_to_v2(id: str, id_expected: str) -> None:
    id_translated = translate_id_v3_to_v2(id)
    assert id_translated == id_expected
