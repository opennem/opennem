"""
Pydantic schema for the AEMO Registrations and Exemptions List spreadsheet data

Available to view at:

https://aemo.com.au/en/energy-systems/electricity/national-electricity-market-nem/participate-in-the-market/registration

Released every month with updates on stations. The parser for the format is at opennem.core.parsers.aemo.rel
"""


from pydantic import validator

from opennem.core.dispatch_type import DispatchType, parse_dispatch_type
from opennem.core.fueltechs import lookup_fueltech
from opennem.core.normalizers import clean_capacity, normalize_duid, participant_name_filter, station_name_cleaner
from opennem.schema.core import BaseConfig


class AEMORelGeneratorRecord(BaseConfig):
    participant: str
    station_name: str
    region: str
    dispatch_type: DispatchType
    category: str
    classification: str
    fuel_source_primary: str
    fuel_source_descriptor: str | None = None
    tech_primary: str | None = None
    tech_primary_descriptor: str | None = None
    unit_no: str
    unit_size: float | None = None
    aggreagation: str
    duid: str | None = None
    reg_cap: float | None = None
    max_cap: float | None = None
    max_roc: float | None = None

    @property
    def fueltech_id(self) -> str | None:
        return lookup_fueltech(
            self.fuel_source_primary,
            self.fuel_source_descriptor,
            self.tech_primary,
            self.tech_primary_descriptor,
            self.dispatch_type,
        )

    _validate_participant = validator("participant", pre=True, allow_reuse=True)(participant_name_filter)
    _validate_station_name = validator("station_name", pre=True, allow_reuse=True)(station_name_cleaner)
    _validate_dispatch_type = validator("dispatch_type", pre=True, allow_reuse=True)(parse_dispatch_type)

    _validate_unit_size = validator("unit_size", pre=True, allow_reuse=True)(lambda x: clean_capacity(x))

    _validate_duid = validator("duid", pre=True, allow_reuse=True)(normalize_duid)

    _validate_reg_cap = validator("reg_cap", pre=True, allow_reuse=True)(lambda x: clean_capacity(x))
    _validate_max_cap = validator("max_cap", pre=True, allow_reuse=True)(lambda x: clean_capacity(x))
    _validate_max_roc = validator("max_roc", pre=True, allow_reuse=True)(lambda x: clean_capacity(x))
