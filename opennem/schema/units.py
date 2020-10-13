from typing import Optional

from pydantic import Field

from .core import BaseConfig


class UnitDefinition(BaseConfig):
    name: str = Field(..., description="Name of the unit")
    name_alias: Optional[str] = Field(None, description="Name alias")
    unit_type: str = Field(..., description="Type of unit")
    round_to: int = 2
    unit: str = Field(..., description="Unit abbreviation")

