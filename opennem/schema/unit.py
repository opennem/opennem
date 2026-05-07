"""
Schema for facility units

"""

import enum
from datetime import datetime

from pydantic import BaseModel, Field

from opennem.schema.field_types import DUIDType, RoundedFloat2, RoundedFloat4


class UnitDispatchType(enum.Enum):
    """How a unit participates in dispatch.

    Attributes:
        GENERATOR: Generates electricity (sends to grid).
        LOAD: Consumes electricity (draws from grid).
        BIDIRECTIONAL: Both generates and consumes (e.g. battery, pumped hydro).
    """

    GENERATOR = "GENERATOR"
    LOAD = "LOAD"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class UnitStatusType(enum.Enum):
    """Operational lifecycle stage of a generating unit.

    Attributes:
        committed: Approved / under construction; not yet generating.
        operating: Currently dispatching to the market.
        retired: Permanently decommissioned.
    """

    committed = "committed"
    operating = "operating"
    retired = "retired"


class UnitFueltechType(enum.Enum):
    """Fueltech classification of a generating unit.

    Identifies the primary fuel or technology a unit uses. Use
    `UnitFueltechGroupType` for higher-level groupings (e.g. all gas
    sub-types collapse to `gas`).

    Attributes:
        battery: Generic battery (use `battery_charging` / `battery_discharging` for direction).
        battery_charging: Battery in charging direction (load).
        battery_discharging: Battery in discharging direction (generator).
        bioenergy_biogas: Biogas combustion.
        bioenergy_biomass: Biomass combustion.
        coal_black: Black-coal thermal plant.
        coal_brown: Brown-coal (lignite) thermal plant.
        distillate: Distillate / diesel-fired generator.
        gas_ccgt: Combined-cycle gas turbine.
        gas_ocgt: Open-cycle gas turbine.
        gas_recip: Gas reciprocating engine.
        gas_steam: Gas-fired steam plant.
        gas_wcmg: Waste coal-mine gas.
        hydro: Conventional hydroelectric generation.
        pumps: Pumped-hydro pumping (load) phase.
        solar_rooftop: Distributed rooftop PV.
        solar_thermal: Concentrated solar thermal.
        solar_utility: Utility-scale PV.
        nuclear: Nuclear (currently unused in AU).
        other: Other / unclassified.
        solar: Generic solar (use `solar_rooftop` / `solar_utility` where known).
        wind: Onshore wind.
        wind_offshore: Offshore wind.
        imports: Network import flow (synthetic unit).
        exports: Network export flow (synthetic unit).
        interconnector: Interconnector (synthetic unit).
        aggregator_vpp: Virtual power plant aggregation.
        aggregator_dr: Demand-response aggregation.
    """

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


class UnitFueltechGroupType(enum.Enum):
    """Higher-level grouping of `UnitFueltechType` values.

    Each group rolls up several `UnitFueltechType` entries — e.g. `gas`
    covers `gas_ccgt`, `gas_ocgt`, `gas_recip`, `gas_steam`, `gas_wcmg`.

    Attributes:
        solar: All solar sub-types.
        wind: Onshore + offshore wind.
        hydro: Conventional hydroelectric.
        biomass: Biogas + biomass combustion.
        coal: Black + brown coal.
        gas: All gas-fired technologies.
        battery: Generic battery aggregation.
        battery_charging: Battery charging direction.
        battery_discharging: Battery discharging direction.
        distillate: Distillate / diesel generation.
        bioenergy: Bioenergy umbrella group.
        pumps: Pumped-hydro pumping phase.
    """

    solar = "solar"
    wind = "wind"
    hydro = "hydro"
    biomass = "biomass"
    coal = "coal"
    gas = "gas"
    battery = "battery"
    battery_charging = "battery_charging"
    battery_discharging = "battery_discharging"
    distillate = "distillate"
    bioenergy = "bioenergy"
    pumps = "pumps"


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
    emission_factor_source: str | None = None
    expected_closure_date: datetime | None = None
    expected_closure_date_specificity: str | None = None  # day, month, quarter, year
    expected_closure_date_source: str | None = None
    expected_operation_date: datetime | None = None
    expected_operation_date_specificity: str | None = None  # day, month, quarter, year
    expected_operation_date_source: str | None = None
    commencement_date: datetime | None = None
    commencement_date_specificity: str | None = None  # day, month, year
    closure_date: datetime | None = None
    closure_date_specificity: str | None = None  # day, month, year

    # Construction fields
    construction_start_date: datetime | None = None
    construction_start_date_specificity: str | None = None  # day, month, year
    construction_start_date_source: str | None = None
    construction_cost: RoundedFloat2 | None = None  # $ AUD Millions
    construction_cost_source: str | None = None

    # Project approval fields
    project_approval_date: datetime | None = None
    project_approval_date_specificity: str | None = None  # day, month, year
    project_approval_date_source: str | None = None
    project_approval_lodgement_date: datetime | None = None

    cms_id: str | None = Field(None, alias="_id")
    cms_created_at: datetime | None = Field(None, alias="_createdAt")
    cms_updated_at: datetime | None = Field(None, alias="_updatedAt")

    class Config:
        extra = "allow"
