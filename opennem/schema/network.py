from datetime import timezone
from typing import Optional

from pydantic import Field

from opennem.utils.timezone import get_current_timezone, get_fixed_timezone

from .core import BaseConfig


class NetworkSchema(BaseConfig):
    code: str
    country: str
    label: str
    timezone: Optional[str] = Field(None, description="Network timezone")
    timezone_database: Optional[str] = Field(
        None, description="Database timezone format"
    )
    offset: Optional[int] = Field(
        None, description="Network time offset in minutes"
    )
    interval_size: int = Field(
        ..., description="Size of network interval in minutes"
    )

    def get_timezone(self) -> timezone:
        if self.offset:
            return get_fixed_timezone(self.offset)
        if self.timezone:
            return timezone(self.timezone)
        return get_current_timezone()


NetworkNEM = NetworkSchema(
    code="NEM",
    label="NEM",
    country="au",
    timezone_database="AEST",
    offset=600,
    interval_size=5,
)
NetworkWEM = NetworkSchema(
    code="WEM",
    label="WEM",
    country="au",
    timezone_database="AWST",
    offset=480,
    interval_size=30,
)


NETWORKS = [NetworkNEM, NetworkWEM]
