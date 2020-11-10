from datetime import timezone as timezone_native
from typing import List, Optional, Union

from pydantic import Field
from pytz import timezone as pytz_timezone

from opennem.utils.timezone import get_current_timezone, get_fixed_timezone

from .core import BaseConfig


class NetworkNetworkRegion(BaseConfig):
    code: str


class NetworkSchema(BaseConfig):
    code: str
    country: str
    label: str

    regions: Optional[List[NetworkNetworkRegion]]
    timezone: Optional[str] = Field(None, description="Network timezone")
    timezone_database: Optional[str] = Field(
        "UTC", description="Database timezone format"
    )
    offset: Optional[int] = Field(
        None, description="Network time offset in minutes"
    )
    interval_size: int = Field(
        ..., description="Size of network interval in minutes"
    )

    def get_timezone(
        self, postgres_format=False
    ) -> Union[timezone_native, pytz_timezone]:
        tz = get_current_timezone()

        if self.offset:
            tz = get_fixed_timezone(self.offset)
        if self.timezone:
            tz = pytz_timezone(self.timezone)

        if postgres_format:
            tz = str(tz)[:3]

        return tz

    @property
    def intervals_per_hour(self):
        return 60 / self.interval_size


class NetworkRegion(BaseConfig):
    code: str
    network: NetworkSchema

    timezone: Optional[str] = Field(None, description="Network timezone")
    timezone_database: Optional[str] = Field(
        "UTC", description="Database timezone format"
    )
    offset: Optional[int] = Field(
        None, description="Network time offset in minutes"
    )


# @TODO move this to db + fixture

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

NetworkAPVI = NetworkSchema(
    code="APVI",
    label="APVI",
    country="au",
    timezone_database="AEST",
    offset=600,
    interval_size=15,
)

NetworkAU = NetworkSchema(
    code="AU",
    label="AU",
    country="au",
    timezone_database="AEST",
    offset=600,
    interval_size=30,
)

NETWORKS = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAU]
