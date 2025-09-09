"""
Facilities API Schema

Defines the schema for the facilities API endpoint responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from opennem.core.networks import network_from_network_code
from opennem.schema.field_types import RoundedFloat2, RoundedFloat4
from opennem.schema.unit import UnitDispatchType, UnitFueltechType, UnitStatusType


class UnitResponse(BaseModel):
    """Unit response schema with selected fields"""

    code: str
    fueltech_id: UnitFueltechType | None
    status_id: UnitStatusType | None
    capacity_registered: RoundedFloat2 | None
    capacity_maximum: RoundedFloat4 | None
    capacity_storage: RoundedFloat4 | None
    emissions_factor_co2: RoundedFloat4 | None
    data_first_seen: datetime | None
    data_last_seen: datetime | None
    dispatch_type: UnitDispatchType

    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

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

        return self


class FacilityResponse(BaseModel):
    """Facility response schema with selected fields and associated units"""

    code: str
    name: str
    network_id: str
    network_region: str
    description: str | None
    npi_id: str | None
    location: dict | None  # Will contain lat/lng from PostGIS geometry
    units: list[UnitResponse]

    updated_at: datetime | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def add_network_to_units(self) -> Any:
        """Add network_id to unit context for timezone conversion."""
        # Create context with network_id for units
        context = {"network_id": self.network_id}

        # Update each unit's context with the network_id
        for unit in self.units:
            unit.model_config["context"] = context

        return self
