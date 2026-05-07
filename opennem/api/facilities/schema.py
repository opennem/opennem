"""
Facilities API Schema

Defines the schema for the facilities API endpoint responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

from opennem.api.schema import APIV4ResponseSchema
from opennem.core.networks import network_from_network_code
from opennem.schema.field_types import RoundedFloat2, RoundedFloat4
from opennem.schema.unit import UnitDispatchType, UnitFueltechType, UnitStatusType


class UnitDateSpecificity(Enum):
    """Granularity of a unit-related date field.

    Many facility lifecycle dates (commencement, closure, construction
    start, project approval) are only known to a coarser granularity than
    a specific calendar day. The matching `*_specificity` field signals
    which components of the paired date are authoritative.

    Attributes:
        YEAR: Only the year is authoritative; month/day are placeholders.
        MONTH: Year + month are authoritative; day is a placeholder.
        QUARTER: Calendar quarter is authoritative.
        DAY: Full calendar day is authoritative.
    """

    YEAR = "year"
    MONTH = "month"
    QUARTER = "quarter"
    DAY = "day"


class UnitResponseSchema(BaseModel):
    """Unit response schema with selected fields"""

    code: str = Field(
        description="Unique unit identifier within the facility (e.g. `BAYSW1`).",
        examples=["BAYSW1"],
    )
    code_display: str | None = Field(
        default=None,
        description="Display-friendly version of the unit code, when distinct from `code`.",
        examples=["Bayswater 1"],
    )
    fueltech_id: UnitFueltechType = Field(
        description="Fueltech classification (e.g. `coal_black`, `solar_utility`, `wind`, `battery_charging`).",
        examples=["coal_black"],
    )
    status_id: UnitStatusType = Field(
        description="Operational status (`operating`, `committed`, `retired`, …).",
        examples=["operating"],
    )
    capacity_registered: RoundedFloat2 | None = Field(
        default=None,
        description="Registered nameplate capacity in MW.",
        examples=[660.0],
    )
    capacity_maximum: RoundedFloat4 | None = Field(
        default=None,
        description="Demonstrated maximum capacity in MW.",
        examples=[680.5],
    )
    capacity_storage: RoundedFloat4 | None = Field(
        default=None,
        description="Storage capacity in MWh (batteries / pumped hydro). `null` for non-storage units.",
        examples=[150.0],
    )
    emissions_factor_co2: RoundedFloat4 | None = Field(
        default=None,
        description="CO2-equivalent emissions intensity in tCO2/MWh.",
        examples=[0.95],
    )
    data_first_seen: datetime | None = Field(
        default=None,
        description="Earliest interval observed for this unit in OE's dispatch data (network-local time).",
        examples=["2010-01-01T04:30:00+10:00"],
    )
    data_last_seen: datetime | None = Field(
        default=None,
        description="Most recent interval observed for this unit (network-local time).",
        examples=["2024-09-01T14:30:00+10:00"],
    )
    dispatch_type: UnitDispatchType | None = Field(
        default=None,
        description="Dispatch type — generator, load, or bidirectional (e.g. battery).",
        examples=["GENERATOR"],
    )

    # unit date fields
    commencement_date: datetime | None = Field(
        default=None,
        description="Date the unit first commenced operations.",
        examples=["1985-12-15T00:00:00+10:00"],
    )
    commencement_date_specificity: UnitDateSpecificity | None = Field(
        default=None,
        description="Granularity of `commencement_date` — `year` means the day/month are not authoritative.",
        examples=["year"],
    )
    commencement_date_display: str | None = Field(
        default=None,
        description="Human-readable rendering of `commencement_date` honoring its specificity.",
        examples=["1985"],
    )
    closure_date: datetime | None = Field(default=None, description="Date the unit was retired.")
    closure_date_display: str | None = Field(default=None, description="Human-readable rendering of `closure_date`.")
    closure_date_specificity: UnitDateSpecificity | None = Field(default=None, description="Granularity of `closure_date`.")
    expected_operation_date: datetime | None = Field(
        default=None, description="Date the unit is expected to commence operations."
    )
    expected_operation_date_specificity: UnitDateSpecificity | None = Field(
        default=None, description="Granularity of `expected_operation_date`."
    )
    expected_operation_date_display: str | None = Field(
        default=None, description="Human-readable rendering of `expected_operation_date`."
    )
    expected_closure_date: datetime | None = Field(default=None, description="Date the unit is expected to retire.")
    expected_closure_date_display: str | None = Field(
        default=None, description="Human-readable rendering of `expected_closure_date`."
    )
    expected_closure_date_specificity: UnitDateSpecificity | None = Field(
        default=None, description="Granularity of `expected_closure_date`."
    )
    construction_start_date: datetime | None = Field(default=None, description="Date construction commenced.")
    construction_start_date_specificity: UnitDateSpecificity | None = Field(
        default=None, description="Granularity of `construction_start_date`."
    )
    construction_start_date_display: str | None = Field(
        default=None, description="Human-readable rendering of `construction_start_date`."
    )
    project_approval_date: datetime | None = Field(default=None, description="Date the project received planning approval.")
    project_approval_date_specificity: UnitDateSpecificity | None = Field(
        default=None, description="Granularity of `project_approval_date`."
    )
    project_approval_date_display: str | None = Field(
        default=None, description="Human-readable rendering of `project_approval_date`."
    )
    project_lodgement_date: datetime | None = Field(default=None, description="Date the project was lodged for approval.")

    # max generation fields
    max_generation: RoundedFloat4 | None = Field(
        default=None,
        description="Highest single-interval generation observed for this unit, in MW.",
        examples=[678.2],
    )
    max_generation_interval: datetime | None = Field(
        default=None,
        description="Interval at which `max_generation` was observed (network-local time).",
        examples=["2023-01-18T16:30:00+10:00"],
    )

    created_at: datetime | None = Field(default=None, description="When this unit record was first created in OE.")
    updated_at: datetime | None = Field(default=None, description="When this unit record was last updated.")

    model_config = ConfigDict(from_attributes=True, defer_build=True)

    @model_validator(mode="after")
    def add_network_timezone(self) -> Any:
        """Add network timezone to datetime fields based on parent facility network."""
        # Get parent context which should contain network_id
        context = self.model_config.get("context", {})
        network_id = context.get("network_id")

        if network_id and (self.data_first_seen or self.data_last_seen):
            network = network_from_network_code(network_id)
            tz_offset = network.get_fixed_offset()

            # Apply timezone to datetime fields if they exist
            if self.data_first_seen:
                self.data_first_seen = self.data_first_seen.replace(tzinfo=tz_offset)
            if self.data_last_seen:
                self.data_last_seen = self.data_last_seen.replace(tzinfo=tz_offset)
            if self.closure_date:
                self.closure_date = self.closure_date.replace(tzinfo=tz_offset)
            if self.expected_closure_date:
                self.expected_closure_date = self.expected_closure_date.replace(tzinfo=tz_offset)
            if self.construction_start_date:
                self.construction_start_date = self.construction_start_date.replace(tzinfo=tz_offset)
            if self.project_approval_date:
                self.project_approval_date = self.project_approval_date.replace(tzinfo=tz_offset)
            if self.project_lodgement_date:
                self.project_lodgement_date = self.project_lodgement_date.replace(tzinfo=tz_offset)
            if self.commencement_date:
                self.commencement_date = self.commencement_date.replace(tzinfo=tz_offset)
            if self.expected_operation_date:
                self.expected_operation_date = self.expected_operation_date.replace(tzinfo=tz_offset)

        return self


class FacilityResponseSchema(BaseModel):
    """Facility response schema with selected fields and associated units"""

    code: str = Field(
        description="Unique facility identifier across the OE platform (e.g. `BAYSW`).",
        examples=["BAYSW"],
    )
    code_display: str | None = Field(
        default=None,
        description="Display-friendly version of `code`, when distinct.",
        examples=["Bayswater Power Station"],
    )
    name: str = Field(
        description="Facility name as published by the network operator.",
        examples=["Bayswater Power Station"],
    )
    network_id: str = Field(
        description="Network the facility participates in — see `/networks` for valid codes.",
        examples=["NEM"],
    )
    network_region: str = Field(
        description="Network region (price zone) the facility sits in.",
        examples=["NSW1"],
    )
    description: str | None = Field(
        default=None,
        description="Free-form description of the facility.",
    )
    npi_id: str | None = Field(
        default=None,
        description="National Pollutant Inventory facility ID, when this facility reports to NPI.",
        examples=["12345"],
    )
    osm_way_id: str | None = Field(
        default=None,
        description="OpenStreetMap way ID for the facility footprint.",
        examples=["123456789"],
    )
    location: dict | None = Field(
        default=None,
        description="GeoJSON `Point` of the facility's nominal location (`lat`/`lng`).",
        examples=[{"lat": -32.4, "lng": 150.95}],
    )
    boundary: dict | None = Field(
        default=None,
        description="GeoJSON `Polygon` or `MultiPolygon` of the facility footprint.",
    )
    units: list[UnitResponseSchema] = Field(
        description="Generating / storage units belonging to this facility.",
    )

    updated_at: datetime | None = Field(default=None, description="When this facility record was last updated.")
    created_at: datetime | None = Field(default=None, description="When this facility record was first created in OE.")

    model_config = ConfigDict(
        from_attributes=True,
        # Exclude None values during serialization
    )

    @model_validator(mode="after")
    def add_network_to_units(self) -> Any:
        """Add network_id to unit context for timezone conversion."""
        # Create context with network_id for units
        context = {"network_id": self.network_id}

        # Update each unit's context with the network_id
        for unit in self.units:
            unit.model_config["context"] = context

        return self


class APIV4FacilityResponseSchema(APIV4ResponseSchema):
    data: list[FacilityResponseSchema] = Field(
        default_factory=list,
        description="Facilities matching the request, sorted by `code`.",
    )

    @model_serializer(mode="wrap")
    def serialize_model(self, serializer, info):
        """Custom serializer to exclude None values from the response."""
        # Get the default serialized data
        data = serializer(self)

        # If we're in JSON mode (which FastAPI uses), exclude None values
        if info.mode == "json":
            return self._remove_none(data)
        return data

    def _remove_none(self, data):
        """Recursively remove None values from a dictionary or list."""
        if isinstance(data, dict):
            return {k: self._remove_none(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self._remove_none(item) for item in data]
        return data
