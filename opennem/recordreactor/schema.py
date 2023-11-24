""" OpenNEM Schema class for a milestone

see matching ORM schema in database. This applies within record reactor and the API output
"""

from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel

from opennem.schema.fueltech import FueltechSchema
from opennem.schema.network import NetworkSchema
from opennem.schema.units import UnitDefinition


class MilestoneType(Enum):
    low = "low"
    average = "average"
    high = "high"


class MilestoneRecord(BaseModel):
    instance_id: UUID4
    record_id: UUID4
    dtime: datetime
    record_type: MilestoneType
    significance: int
    value: int | float
    unit: UnitDefinition
    network: NetworkSchema
    fueltech: FueltechSchema
    description: str | None = None

    @property
    def network_code(self) -> str:
        return self.network.code

    @property
    def country(self) -> str:
        return self.country

    @property
    def fueltech_code(self) -> str:
        return self.fueltech.code

    @property
    def unit_code(self) -> str:
        return self.unit.name
