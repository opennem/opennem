"""OpenNEM Schema class for a milestone

see matching ORM schema in database. This applies within record reactor and the API output
"""

from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, computed_field

from opennem.schema.fueltech_group import FueltechGroupSchema
from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.schema.units import UnitDefinition
from opennem.utils.seasons import map_date_start_to_season

MILESTONE_SUPPORTED_NETWORKS = [NetworkNEM, NetworkWEM]


class MilestoneAggregate(str, Enum):
    low = "low"
    high = "high"


class MilestoneType(str, Enum):
    demand_power = "demand.power"
    demand_energy = "demand.energy"
    price = "price"
    generated_power = "generated.power"
    generated_energy = "generated.energy"
    emissions = "emissions"


class MilestonePeriod(str, Enum):
    interval = "interval"
    day = "day"
    week = "week"
    month = "month"
    quarter = "quarter"
    season = "season"
    year = "year"
    financial_year = "financial_year"


class MilestoneRecordSchema(BaseModel):
    interval: datetime
    aggregate: MilestoneAggregate
    metric: MilestoneType
    period: MilestonePeriod
    unit: UnitDefinition
    network: NetworkSchema
    network_region: str | None = None
    fueltech: FueltechGroupSchema | None = None
    value: int | float | None = None

    @computed_field
    @property
    def record_id(self) -> str:
        """calculate the record_id from the milestone record"""
        return get_milestone_record_id(self)


class MilestoneRecordOutputSchema(BaseModel):
    record_id: str
    interval: datetime
    instance_id: UUID4
    aggregate: str
    metric: str
    period: str
    significance: int
    value: int | float
    value_unit: str
    network_id: str
    network_region: str | None = None
    fueltech_id: str | None = None
    description: str | None = None
    description_long: str | None = None
    previous_instance_id: UUID4 | None = None
    history: list["MilestoneRecordOutputSchema"] | None = None


class MilestoneMetadataSchema(BaseModel):
    aggregates: list[MilestoneAggregate]
    type: list[MilestoneType]
    periods: list[MilestonePeriod]
    networks: list[NetworkSchema]
    network_regions: list[str] | None = None
    fueltechs: list[FueltechGroupSchema]


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
    milestone: MilestoneRecordSchema,
) -> str:
    """Get a record id"""
    record_id_components = [
        "au",
        milestone.network.parent_network or milestone.network.code,
        milestone.network_region,
        milestone.fueltech.code if milestone.fueltech else None,
        milestone.metric.value,
        map_date_start_to_season(milestone.interval) if milestone.period is MilestonePeriod.season else milestone.period.value,
        milestone.aggregate.value,
    ]

    # remove empty items from record id components list and join with a period
    record_id = ".".join(filter(None, record_id_components)).lower()

    return record_id
