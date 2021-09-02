from opennem.core.fueltechs import lookup_fueltech


class TestFueltechMap(object):
    def test_bairnsdale(self):
        subj = lookup_fueltech(
            "Fossil",
            "Natural Gas",
            "Combustion",
            "Open Cycle Gas turbines (OCGT)",
        )

        assert subj == "gas_ocgt", "Bairnsdale is gas_ocgt"

    def test_rel_hydro(self):
        subj = lookup_fueltech(
            "Hydro", "Water", "Renewable", "Hydro - Gravity"
        )

        assert subj == "hydro", "REL hydro fueltech test"

    def test_battery_storage(self):
        subj = lookup_fueltech("Battery storage", "Grid", "Storage", "Battery")

        assert (
            subj == "battery_discharging"
        ), "Fueltech battery storage generator"

    def test_battery_load(self):
        subj = lookup_fueltech(None, None, "Storage", "Battery", "load")

        assert (
            subj == "battery_charging"
        ), "Load storage battery is battery discharging"

    def test_wem_pimjara(self):
        subj = lookup_fueltech("Gas", None, "Gas")

        assert subj == "gas_ocgt", "Pinjara is gas"

    def test_wem_kemberton(self):
        subj = lookup_fueltech("Gas", None, "Dual (Gas / Distillate)")

        assert subj == "gas_ocgt", "Kemberton is gas"
