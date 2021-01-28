from datetime import timezone as timezone_native
from typing import List, Optional, Union

import pytz
from pydantic import Field
from pytz import FixedOffset
from pytz import timezone as pytz_timezone

from opennem.core.time import get_interval_by_size
from opennem.schema.time import TimeInterval
from opennem.utils.timezone import get_current_timezone, get_fixed_timezone

from .core import BaseConfig


class NetworkNetworkRegion(BaseConfig):
    code: str


class NetworkRegionSchema(BaseConfig):
    network_id: str
    code: str
    timezone: Optional[str]


class NetworkSchema(BaseConfig):
    code: str
    country: str
    label: str

    regions: Optional[List[NetworkNetworkRegion]]
    timezone: Optional[str] = Field(None, description="Network timezone")
    timezone_database: str = Field("UTC", description="Database timezone format")
    offset: Optional[int] = Field(None, description="Network time offset in minutes")
    interval_size: int = Field(..., description="Size of network interval in minutes")

    def get_interval(self) -> Optional[TimeInterval]:
        if not self.interval_size:
            return None

        interval = get_interval_by_size(self.interval_size)

        return interval

    def get_timezone(self, postgres_format=False) -> Union[timezone_native, pytz_timezone]:
        tz = get_current_timezone()

        if self.offset:
            tz = get_fixed_timezone(self.offset)
        if self.timezone:
            tz = pytz_timezone(self.timezone)

        if postgres_format:
            tz = str(tz)[:3]

        return tz

    def get_fixed_offset(self) -> FixedOffset:
        if self.offset:
            return pytz.FixedOffset(self.offset)

        raise Exception("No offset set")

    @property
    def intervals_per_hour(self):
        return 60 / self.interval_size


class NetworkRegion(BaseConfig):
    code: str
    network: NetworkSchema

    timezone: Optional[str] = Field(None, description="Network timezone")
    timezone_database: Optional[str] = Field("UTC", description="Database timezone format")
    offset: Optional[int] = Field(None, description="Network time offset in minutes")


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
