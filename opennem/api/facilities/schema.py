"""
Facilities API Schema

Defines the schema for the facilities API endpoint responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer, model_validator

from opennem.api.schema import APIV4ResponseSchema
from opennem.core.networks import network_from_network_code
from opennem.schema.field_types import RoundedFloat2, RoundedFloat4
from opennem.schema.unit import UnitDispatchType, UnitFueltechType, UnitStatusType


class UnitDateSpecificity(Enum):
    """Date specificity enum"""

    YEAR = "year"
    MONTH = "month"
    QUARTER = "quarter"
    DAY = "day"


class UnitResponseSchema(BaseModel):
    """Unit response schema with selected fields"""

    code: str
    fueltech_id: UnitFueltechType
    status_id: UnitStatusType
    capacity_registered: RoundedFloat2 | None = None
    capacity_maximum: RoundedFloat4 | None = None
    capacity_storage: RoundedFloat4 | None = None
    emissions_factor_co2: RoundedFloat4 | None = None
    data_first_seen: datetime | None = None
    data_last_seen: datetime | None = None
    dispatch_type: UnitDispatchType | None = None

    # unit date fields
    commencement_date: datetime | None = None
    commencement_date_specificity: UnitDateSpecificity | None = None
    commencement_date_display: str | None = None
    closure_date: datetime | None = None
    closure_date_display: str | None = None
    closure_date_specificity: UnitDateSpecificity | None = None
    expected_operation_date: datetime | None = None
    expected_operation_date_specificity: UnitDateSpecificity | None = None
    expected_operation_date_display: str | None = None
    expected_closure_date: datetime | None = None
    expected_closure_date_display: str | None = None
    expected_closure_date_specificity: UnitDateSpecificity | None = None
    construction_start_date: datetime | None = None
    construction_start_date_specificity: UnitDateSpecificity | None = None
    construction_start_date_display: str | None = None
    project_approval_date: datetime | None = None
    project_approval_date_specificity: UnitDateSpecificity | None = None
    project_approval_date_display: str | None = None
    project_lodgement_date: datetime | None = None

    # max generation fields
    max_generation: RoundedFloat4 | None = None
    max_generation_interval: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

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

    code: str
    name: str
    network_id: str
    network_region: str
    description: str | None = None
    npi_id: str | None = None
    location: dict | None = None  # Will contain lat/lng from PostGIS geometry
    units: list[UnitResponseSchema]

    updated_at: datetime | None = None
    created_at: datetime | None = None

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
    data: list[FacilityResponseSchema] = []

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
