"""OpenNEM Schema class for a milestone

see matching ORM schema in database. This applies within record reactor and the API output
"""

from datetime import datetime
from enum import Enum

from pydantic import UUID4, BaseModel, Field, computed_field

from opennem.schema.network import NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.seasons import map_date_start_to_season

MILESTONE_SUPPORTED_NETWORKS = [NetworkNEM, NetworkWEM]


class MilestoneAggregate(str, Enum):
    """
    Enum representing different types of aggregates for milestones in the OpenNEM project.

    These aggregates are used to summarise data over different time intervals.

    This determines the type of aggregation that is applied to the data.
    """

    low = "low"
    high = "high"


class MilestoneType(str, Enum):
    """
    Enum representing different types of milestones in the OpenNEM project.

    These types are used to categorise and analyse energy production and consumption
    across various technologies in the Australian electricity system.

    This determines the source of data and query for the milestone.
    """

    power = "power"
    energy = "energy"
    demand = "demand"
    price = "price"
    market_value = "market_value"
    emissions = "emissions"
    proportion = "proportion"


class MilestoneUnit(str, Enum):
    """
    Enum representing different units for milestones in the OpenNEM project.

    These units are used to define the unit of measure for a milestone.
    """

    power = "power"
    energy = "energy"
    price = "price"
    market_value = "market_value"
    emissions = "emissions"
    renewable_proportion = "renewable_proportion"


class MilestonePeriod(str, Enum):
    """
    Enum representing different periods for milestones in the OpenNEM project.

    These periods are used to aggregate data over different time intervals.

    This determines the window of time that a milestone covers. ie. the start and end dates in queries
    """

    interval = "interval"
    day = "day"
    week_rolling = "7d"
    month = "month"
    quarter = "quarter"
    season = "season"
    year = "year"
    financial_year = "financial_year"


class MilestoneFueltechGrouping(str, Enum):
    """
    Enum representing different fuel technology groupings for milestones in the OpenNEM project.

    These groupings are used to categorise and analyse energy production and consumption
    across various technologies in the Australian electricity system.
    """

    battery_charging = "battery_charging"
    battery_discharging = "battery_discharging"
    bioenergy = "bioenergy"
    coal = "coal"
    demand = "demand"
    distillate = "distillate"
    gas = "gas"
    hydro = "hydro"
    pumps = "pumps"
    solar = "solar"
    wind = "wind"
    renewables = "renewables"
    fossils = "fossils"


# Models


class MilestoneUnitSchema(BaseModel):
    """ """

    name: str
    label: str
    unit: str
    output_format: str


class MilestoneTypeSchema(BaseModel):
    """ """

    name: str
    label: str
    unit: str
    description: str
    significance_weight: float
    periods: list[MilestonePeriod] = Field(default=[], description="The periods that this milestone type is applicable for")


class MilestoneRecordSchema(BaseModel):
    """
    Internal representation of a milestone record

    """

    interval: datetime
    aggregate: MilestoneAggregate
    metric: MilestoneType
    period: MilestonePeriod
    network: NetworkSchema
    unit: MilestoneUnitSchema
    network_region: str | None = None
    fueltech: MilestoneFueltechGrouping | None = None
    value: int | float | None = None

    @computed_field
    @property
    def record_id(self) -> str:
        """calculate the record_id from the milestone record"""
        return get_milestone_record_id(self)

    # @computed_field
    # @property
    # def unit(self) -> MilestoneUnitSchema:
    #     """get the unit schema for the milestone record"""
    #     return get_milestone_unit(self.metric)


class MilestoneRecordOutputSchema(BaseModel):
    """
    API output schema for a milestone record
    """

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
    """
    Metadata schema for a milestone
    """

    aggregates: list[MilestoneAggregate]
    milestone_type: list[MilestoneType]
    periods: list[MilestonePeriod]
    units: dict[str, MilestoneUnitSchema]
    fueltechs: list[MilestoneFueltechGrouping]
    networks: list[NetworkSchema]
    network_regions: list[str] | None = None


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
        milestone.fueltech if milestone.fueltech else None,
        milestone.metric.value,
        map_date_start_to_season(milestone.interval) if milestone.period is MilestonePeriod.season else milestone.period.value,
        milestone.aggregate.value,
    ]

    # remove empty items from record id components list and join with a period
    record_id = ".".join(filter(None, record_id_components)).lower()

    return record_id
