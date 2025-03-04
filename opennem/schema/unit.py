"""
Schema for facility units

"""

import enum
from datetime import date

from pydantic import BaseModel

from opennem.schema.field_types import DUIDType, RoundedFloat2, RoundedFloat4


class UnitDispatchType(enum.Enum):
    GENERATOR = "GENERATOR"
    LOAD = "LOAD"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class UnitStatusType(enum.Enum):
    committed = "committed"
    operating = "operating"
    retired = "retired"


class UnitFueltechType(enum.Enum):
    battery = "battery"
    battery_charging = "battery_charging"
    battery_discharging = "battery_discharging"
    bioenergy_biogas = "bioenergy_biogas"
    bioenergy_biomass = "bioenergy_biomass"
    coal_black = "coal_black"
    coal_brown = "coal_brown"
    distillate = "distillate"
    gas_ccgt = "gas_ccgt"
    gas_ocgt = "gas_ocgt"
    gas_recip = "gas_recip"
    gas_steam = "gas_steam"
    gas_wcmg = "gas_wcmg"
    hydro = "hydro"
    pumps = "pumps"
    solar_rooftop = "solar_rooftop"
    solar_thermal = "solar_thermal"
    solar_utility = "solar_utility"
    nuclear = "nuclear"
    other = "other"
    solar = "solar"
    wind = "wind"
    wind_offshore = "wind_offshore"
    imports = "imports"
    exports = "exports"
    interconnector = "interconnector"
    aggregator_vpp = "aggregator_vpp"
    aggregator_dr = "aggregator_dr"


class UnitSchema(BaseModel):
    """Facility output schema"""

    code: DUIDType
    dispatch_type: UnitDispatchType
    fueltech_id: UnitFueltechType
    status_id: UnitStatusType
    capacity_registered: RoundedFloat2 | None = None
    capacity_maximum: RoundedFloat2 | None = None
    storage_capacity: RoundedFloat2 | None = None
    emissions_factor_co2: RoundedFloat4 | None = None
    expected_closure_date: date | None = None
    commencement_date: date | None = None
    closure_date: date | None = None
