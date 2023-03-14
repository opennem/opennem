from opennem.core.units import UNIT_TYPES_SUPPORTED, get_unit
from opennem.schema.units import UnitDefinition


class TestSchemaUnits:
    def test_loading(self):
        schema = UnitDefinition(name="power", unit_type="power", unit="MW")

        assert schema.name == "power", "Unit is power"
        assert schema.unit_type == "power", "Unit type is power"
        assert schema.unit == "MW", "Unit def is MW"

    def test_fixture_loaded(self):
        assert "power" in UNIT_TYPES_SUPPORTED, "We have power unit"
        assert "energy" in UNIT_TYPES_SUPPORTED, "We have energy unit"

    def test_load_unit(self):
        power = get_unit("power")

        assert isinstance(power, UnitDefinition), "Returns a definition"
        assert power.name == "power_mega", "Returns power name"
        assert power.name_alias == "power", "Returns power name"
        assert power.unit == "MW", "Schema returns correct unit"
