import pytest

from opennem.core.compat.utils import translate_id_v2_to_v3, translate_id_v3_to_v2


@pytest.mark.parametrize(
    ["id", "id_expected"],
    [
        ("nem.tas1.fuel_tech.coal_black.energy", "tas1.fuel_tech.black_coal.energy"),
        ("nem.tas1.fuel_tech.coal_black.power", "tas1.fuel_tech.black_coal.power"),
        ("nem.tas1.fuel_tech.wind.power", "tas1.fuel_tech.wind.power"),
        ("nem.tas1.price", "tas1.price"),
        ("nem.tas1.temperature", "tas1.temperature"),
        ("nem.tas1.temperature_mean", "tas1.temperature_mean"),
        ("nem.tas1.fuel_tech.gas_ocgt.market_value", "tas1.fuel_tech.gas_ocgt.market_value"),
        ("nem.tas1.fuel_tech.coal_black.market_value", "tas1.fuel_tech.black_coal.market_value"),
        ("nem.tas1.fuel_tech.solar_rooftop.energy", "tas1.fuel_tech.rooftop_solar.energy"),
        ("nem.tas1.fuel_tech.imports.emissions", "tas1.fuel_tech.imports.emissions"),
        ("nem.tas1.demand", "tas1.demand"),
        # same but with region changed
        ("nem.nsw1.fuel_tech.coal_black.energy", "nsw1.fuel_tech.black_coal.energy"),
        ("nem.nsw1.fuel_tech.coal_black.power", "nsw1.fuel_tech.black_coal.power"),
        ("nem.nsw1.fuel_tech.wind.power", "nsw1.fuel_tech.wind.power"),
        ("nem.nsw1.price", "nsw1.price"),
        ("nem.nsw1.temperature", "nsw1.temperature"),
        ("nem.nsw1.temperature_mean", "nsw1.temperature_mean"),
        ("nem.nsw1.fuel_tech.gas_ocgt.market_value", "nsw1.fuel_tech.gas_ocgt.market_value"),
        ("nem.nsw1.fuel_tech.coal_black.market_value", "nsw1.fuel_tech.black_coal.market_value"),
        ("nem.nsw1.fuel_tech.solar_rooftop.energy", "nsw1.fuel_tech.rooftop_solar.energy"),
        ("nem.nsw1.fuel_tech.imports.emissions", "nsw1.fuel_tech.imports.emissions"),
        ("nem.nsw1.demand", "nsw1.demand"),
        # same but with country added changed
        ("au.nem.nsw1.fuel_tech.coal_black.energy", "nsw1.fuel_tech.black_coal.energy"),
        ("au.nem.nsw1.fuel_tech.coal_black.power", "nsw1.fuel_tech.black_coal.power"),
        ("au.nem.nsw1.fuel_tech.wind.power", "nsw1.fuel_tech.wind.power"),
        ("au.nem.nsw1.price", "nsw1.price"),
        ("au.nem.nsw1.temperature", "nsw1.temperature"),
        ("au.nem.nsw1.temperature_mean", "nsw1.temperature_mean"),
        ("au.nem.nsw1.fuel_tech.gas_ocgt.market_value", "nsw1.fuel_tech.gas_ocgt.market_value"),
        (
            "au.nem.nsw1.fuel_tech.coal_black.market_value",
            "nsw1.fuel_tech.black_coal.market_value",
        ),
        ("au.nem.nsw1.fuel_tech.solar_rooftop.energy", "nsw1.fuel_tech.rooftop_solar.energy"),
        ("au.nem.nsw1.fuel_tech.imports.emissions", "nsw1.fuel_tech.imports.emissions"),
        ("au.nem.nsw1.demand", "nsw1.demand"),
        #
        ("nem.nsw1.fuel_tech.coal_brown.power", "nsw1.fuel_tech.brown_coal.power"),
    ],
)
def test_translate_id_v3_to_v2(id: str, id_expected: str) -> None:
    id_translated = translate_id_v3_to_v2(id)
    assert id_translated == id_expected


@pytest.mark.parametrize(
    ["id_expected", "id"],
    [
        ("au.nem.tas1.fuel_tech.coal_black.energy", "tas1.fuel_tech.black_coal.energy"),
        ("au.nem.tas1.fuel_tech.coal_black.power", "tas1.fuel_tech.black_coal.power"),
        ("au.nem.tas1.fuel_tech.wind.power", "tas1.fuel_tech.wind.power"),
        ("au.nem.tas1.price", "tas1.price"),
        ("au.nem.tas1.temperature", "tas1.temperature"),
        ("au.nem.tas1.temperature_mean", "tas1.temperature_mean"),
        ("au.nem.tas1.fuel_tech.gas_ocgt.market_value", "tas1.fuel_tech.gas_ocgt.market_value"),
        (
            "au.nem.tas1.fuel_tech.coal_black.market_value",
            "tas1.fuel_tech.black_coal.market_value",
        ),
        ("au.nem.tas1.fuel_tech.solar_rooftop.energy", "tas1.fuel_tech.rooftop_solar.energy"),
        ("au.nem.tas1.fuel_tech.imports.emissions", "tas1.fuel_tech.imports.emissions"),
        ("au.nem.tas1.demand", "tas1.demand"),
    ],
)
def test_translate_id_v2_to_v3(id_expected: str, id: str) -> None:
    id_translated = translate_id_v2_to_v3(id)
    assert id_translated == id_expected
