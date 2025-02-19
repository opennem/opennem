"""
Facilities API Schema

Defines the schema for the facilities API endpoint responses.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from opennem.schema.field_types import RoundedFloat2, RoundedFloat4
from opennem.schema.unit import UnitDispatchType, UnitFueltechType, UnitStatusType


class UnitResponse(BaseModel):
    """Unit response schema with selected fields"""

    code: str
    fueltech_id: UnitFueltechType | None
    status_id: UnitStatusType | None
    capacity_registered: RoundedFloat2 | None
    emissions_factor_co2: RoundedFloat4 | None
    data_first_seen: datetime | None
    data_last_seen: datetime | None
    dispatch_type: UnitDispatchType

    model_config = ConfigDict(from_attributes=True)


class FacilityResponse(BaseModel):
    """Facility response schema with selected fields and associated units"""

    code: str
    name: str
    network_id: str
    network_region: str
    description: str | None
    units: list[UnitResponse]

    model_config = ConfigDict(from_attributes=True)
