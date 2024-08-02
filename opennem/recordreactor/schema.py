"""OpenNEM Schema class for a milestone

see matching ORM schema in database. This applies within record reactor and the API output
"""

from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, computed_field

from opennem.schema.fueltech import FueltechSchema
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.schema.units import UnitDefinition

MILESTONE_SUPPORTED_NETWORKS = [NetworkNEM, NetworkWEM]


class MilestoneAggregate(str, Enum):
    low = "low"
    high = "high"


class MilestoneMetric(str, Enum):
    demand = "demand"
    price = "price"
    power = "power"
    energy = "energy"
    emissions = "emissions"


class MilestonePeriod(str, Enum):
    interval = "interval"
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    year = "year"
    financial_year = "financial_year"


class MilestoneSchema(BaseModel):
    aggregate: MilestoneAggregate
    metric: MilestoneMetric
    period: MilestonePeriod
    network_id: NetworkSchema
    network_region: str | None = None
    fueltech_id: FueltechSchema | None = None
    fueltech_group_id: FueltechSchema | str | None = None

    @computed_field
    @property
    def record_id(self) -> str:
        """calculate the record_id from the milestone record"""
        return get_milestone_record_id(self)

    @property
    def fueltech_label(self) -> str:
        """get the fueltech label"""
        return self.fueltech_id.label if self.fueltech_id else ""


class MilestoneRecord(BaseModel):
    record_id: str
    interval: datetime
    instance_id: UUID4
    aggregate: MilestoneAggregate
    metric: MilestoneMetric | None = None
    period: str | None = None
    significance: int
    value: int | float
    value_unit: UnitDefinition | None = None
    network_id: NetworkSchema | str | None = None
    network_region: str | None = None
    fueltech_id: FueltechSchema | None = None
    fueltech_group_id: FueltechSchema | str | None = None
    description: str | None = None
    description_long: str | None = None
    previous_record_id: str | None = None

    @property
    def network_code(self) -> str:
        return self.network_id.code if self.network_id else ""

    @property
    def country(self) -> str:
        return self.country

    @property
    def fueltech_code(self) -> str:
        return self.fueltech_id.code if self.fueltech_id else ""

    @property
    def unit_code(self) -> str | None:
        return self.value_unit.name if self.value_unit else None


def get_milestone_network_id_map(network_id: str) -> str:
    """Get a network id map"""
    network_id_map = {
        "AEMO_ROOFTOP": "NEM",
        "APVI": "WEM",
    }

    if network_id not in network_id_map:
        return network_id

    return network_id_map[network_id]


def get_milestone_record_id(
    milestone: MilestoneSchema,
) -> str:
    """Get a record id"""
    record_id_components = [
        "au",
        milestone.network_id.code,
        milestone.network_region,
        milestone.fueltech_id,
        milestone.metric.value,
        milestone.period.value,
        milestone.aggregate.value,
    ]

    # remove empty items from record id components list and join with a period
    record_id = ".".join(filter(None, record_id_components)).lower()

    return record_id
