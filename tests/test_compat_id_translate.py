import pytest

from opennem.core.compat import translate_id_v3_to_v2


@pytest.mark.parametrize(
    ["id", "id_expected"],
    [
        ("nem.tas1.fuel_tech.black_coal.energy", "tas1.fuel_tech.coal_black.energy"),
        ("nem.tas1.fuel_tech.black_coal.power", "tas1.fuel_tech.coal_black.power"),
        ("nem.tas1.fuel_tech.wind.power", "tas1.fuel_tech.wind.power"),
        ("nem.tas1.price", "tas1.price"),
        ("nem.tas1.temperature.094029.temperature", "tas1.temperature"),
    ],
)
def test_translate_id_v3_to_v2(id: str, id_expected: str) -> None:
    id_translated = translate_id_v3_to_v2(id)
    assert id_translated == id_expected
