"""OpenNEM Schema class for a milestone

see matching ORM schema in database. This applies within record reactor and the API output
"""

from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel

from opennem.schema.fueltech import FueltechSchema
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.schema.units import UnitDefinition

MILESTONE_SUPPORTED_NETWORKS = [NetworkNEM, NetworkWEM]


class MilestoneAggregate(str, Enum):
    low = "low"
    average = "average"
    high = "high"


class MilestoneMetric(str, Enum):
    demand = "demand"
    price = "price"
    generation = "generation"
    energy = "energy"
    emissions = "emissions"


class MilestonePeriods(str, Enum):
    interval = "interval"
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"
    financial_year = "financial_year"


class MilestoneRecord(BaseModel):
    instance_id: UUID4
    record_id: str
    interval: datetime
    aggregate: MilestoneAggregate
    significance: int
    value: int | float
    unit: UnitDefinition | str | None = None
    network: NetworkSchema | str | None = None
    network_region: str | None = None
    fueltech: FueltechSchema | str | None = None
    description: str | None = None
    period: str | None = None
    previous_record_id: str | None = None
    metric: MilestoneMetric | None = None

    @property
    def network_code(self) -> str:
        return self.network.code if self.network else ""

    @property
    def country(self) -> str:
        return self.country

    @property
    def fueltech_code(self) -> str:
        return self.fueltech.code if self.fueltech else ""

    @property
    def unit_code(self) -> str | None:
        return self.unit.name if self.unit else None
