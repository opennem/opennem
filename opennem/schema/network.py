""" Defines a schema for different supported energy networks


"""
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any, List, Optional, Union
from zoneinfo import ZoneInfo

from pydantic import Field

from opennem import settings
from opennem.core.time import get_interval_by_size
from opennem.schema.time import TimeInterval

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

    timezone: str = Field(..., description="Network timezone")

    timezone_database: str = Field("UTC", description="Database timezone format")

    offset: Optional[int] = Field(None, description="Network time offset in minutes")

    interval_size: int = Field(..., description="Size of network interval in minutes")

    interval_shift: int = Field(0, description="Size of reading shift in minutes")

    # support hardcoded first seen
    data_first_seen: datetime | None
    price_first_seen: datetime | None
    interconnector_first_seen: datetime | None
    rooftop_first_seen: datetime | None

    def get_interval(self) -> Optional[TimeInterval]:
        if not self.interval_size:
            return None

        interval = get_interval_by_size(self.interval_size)

        return interval

    def get_timezone(self, postgres_format: bool = False) -> ZoneInfo | str:
        """Get the network timezone

        @TODO define crawl timezones vs network timezone
        @TODO clean this up and separate out postres format to another parameter
        """
        tz: ZoneInfo | str | None = None

        # If a fixed offset is defined for the network use that
        if self.offset:
            tz = timezone(timedelta(seconds=self.offset * 60))  # type: ignore

        # If the network alternatively defines a timezone
        if not tz and self.timezone:
            tz = ZoneInfo(self.timezone)

        if postgres_format:
            return str(tz)[:3]

        return tz

    def get_crawl_timezone(self) -> Any:
        tz = ZoneInfo(self.timezone)

        return tz

    def get_fixed_offset(self) -> Union[Any, tzinfo]:
        if not self.offset:
            raise Exception("No offset set")

        return timezone(timedelta(seconds=self.offset * 60))

    @property
    def intervals_per_hour(self) -> float:
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
    timezone="Australia/Brisbane",
    timezone_database="AEST",
    offset=600,
    interval_size=5,
    interval_shift=5,
    data_first_seen=datetime.fromisoformat("1998-12-07T01:50:00+10:00"),
)

NetworkWEM = NetworkSchema(
    code="WEM",
    label="WEM",
    country="au",
    timezone="Australia/Perth",
    timezone_database="AWST",
    offset=480,
    interval_size=30,
    data_first_seen=datetime.fromisoformat("2006-09-20T02:00:00+10:00"),
)

NetworkAPVI = NetworkSchema(
    code="APVI",
    label="APVI",
    country="au",
    timezone="Australia/Sydney",
    timezone_database="AEST",
    offset=600,
    interval_size=15,
    data_first_seen=datetime.fromisoformat("2015-03-20T06:15:00+10:00"),
)

# This is a "virtual" network that is made up of
# NEM + WEM
NetworkAU = NetworkSchema(
    code="AU",
    label="AU",
    country="au",
    timezone="Australia/Sydney",
    timezone_database="AEST",
    offset=600,
    interval_size=30,
    data_first_seen=datetime.fromisoformat("1998-12-07T01:50:00+10:00"),
)


NetworkAEMORooftop = NetworkSchema(
    code="AEMO_ROOFTOP",
    label="AEMO Rooftop",
    country="au",
    timezone="Australia/Sydney",
    timezone_database="AEST",
    offset=600,
    interval_size=30,
    data_first_seen=datetime.fromisoformat("2016-08-01T00:30:00+10:00"),
)

# This is the network for derived solar_rooftop data
# that predates AEMORooftop
NetworkAEMORooftopBackfill = NetworkSchema(
    code="AEMO_ROOFTOP_BACKFILL",
    label="AEMO Rooftop Backfill",
    country="au",
    timezone="Australia/Sydney",
    timezone_database="AEST",
    offset=600,
    interval_size=30,
)


NETWORKS = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAU, NetworkAEMORooftop, NetworkAEMORooftop]
