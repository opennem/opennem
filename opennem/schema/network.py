""" Defines a schema for different supported energy networks


"""
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import Field

from opennem.core.fueltechs import ALL_FUELTECH_CODES
from opennem.core.time import get_interval_by_size
from opennem.schema.time import TimeInterval

from .core import BaseConfig

all_fueltechs_without_rooftop = ALL_FUELTECH_CODES.remove("solar_rooftop") if ALL_FUELTECH_CODES else []


class NetworkSchemaException(Exception):
    pass


class NetworkNetworkRegion(BaseConfig):
    code: str


class NetworkRegionSchema(BaseConfig):
    network_id: str
    code: str
    timezone: str | None


class NetworkSchema(BaseConfig):
    code: str
    country: str
    label: str

    regions: list[NetworkNetworkRegion] | None

    timezone: str = Field(..., description="Network timezone")

    timezone_database: str = Field("UTC", description="Database timezone format")

    offset: int | None = Field(None, description="Network time offset in minutes")

    interval_size: int = Field(..., description="Size of network interval in minutes")
    interval_size_price: int | None = Field(None, description="Size of network price interval in minutes")

    interval_shift: int = Field(0, description="Size of reading shift in minutes")

    # support hardcoded first seen
    data_first_seen: datetime | None
    price_first_seen: datetime | None
    interconnector_first_seen: datetime | None
    rooftop_first_seen: datetime | None

    # monitoring settings
    # in minutes, after how long to alert on delays for this network
    monitor_interval_alert_threshold: int | None

    # additional networks that make up this network
    # ex. ROOFTOP, APVI etc.
    subnetworks: list["NetworkSchema"] | None

    # fueltechs provided by this network
    fueltechs: list[str] | None = Field(None, description="Fueltechs provided by this network")

    # Does the network have flows
    has_interconnectors: bool = Field(False, description="Network has interconnectors")

    def __str__(self) -> str:
        """String representation of network schema"""
        return f"NetworkSchema({self.code})"

    def __repr__(self) -> str:
        """String representation of network schema"""
        return f"NetworkSchema({self.code})"

    def get_interval(self) -> TimeInterval | None:
        return get_interval_by_size(self.interval_size) if self.interval_size else None

    def get_timezone(self, postgres_format: bool = False) -> ZoneInfo | str:
        """Get the network timezone

        @TODO define crawl timezones vs network timezone
        @TODO clean this up and separate out postres format to another parameter
        """
        tz: timezone | ZoneInfo | None = timezone(timedelta(seconds=self.offset * 60)) if self.offset else None
        # If the network alternatively defines a timezone
        if not tz and self.timezone:
            tz = ZoneInfo(self.timezone)

        return str(tz)[:3] if postgres_format and tz else tz

    def get_crawl_timezone(self) -> Any:
        return ZoneInfo(self.timezone)

    def get_fixed_offset(self) -> Any | tzinfo:
        if not self.offset:
            raise NetworkSchemaException("No offset set")

        return timezone(timedelta(seconds=self.offset * 60))

    def get_offset_string(self) -> str:
        return str(self.get_fixed_offset()).replace("UTC", "") if isinstance(self.get_fixed_offset(), timezone) else ""

    @property
    def intervals_per_hour(self) -> float:
        return 60 / self.interval_size

    def get_networks_query(self) -> list["NetworkSchema"]:
        """Returns a full list of network and sub-networks for queries"""
        return [self] + self.subnetworks if self.subnetworks else [self]


class NetworkRegion(BaseConfig):
    code: str
    network: NetworkSchema

    timezone: str | None = Field(None, description="Network timezone")
    timezone_database: str | None = Field("UTC", description="Database timezone format")
    offset: int | None = Field(None, description="Network time offset in minutes")


NetworkAPVI = NetworkSchema(
    code="APVI",
    label="APVI",
    country="au",
    timezone="Australia/Sydney",
    timezone_database="AEST",
    offset=600,
    interval_size=15,
    data_first_seen=datetime.fromisoformat("2015-03-20T06:15:00+10:00"),
    fueltechs=["solar_rooftop"],
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
    fueltechs=["solar_rooftop"],
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
    fueltechs=["solar_rooftop"],
)


NetworkNEM = NetworkSchema(
    code="NEM",
    label="NEM",
    country="au",
    timezone="Australia/Brisbane",
    timezone_database="AEST",
    offset=600,
    interval_size=5,
    interval_size_price=5,
    interval_shift=5,
    data_first_seen=datetime.fromisoformat("1998-12-07T01:50:00+10:00"),
    price_first_seen=datetime.fromisoformat("2009-07-01T00:00:00+10:00"),
    interconnector_first_seen=datetime.fromisoformat("2010-01-01T00:00:00+10:00"),
    rooftop_first_seen=datetime.fromisoformat("2007-01-01T00:00:00+10:00"),
    monitor_interval_alert_threshold=10,
    has_interconnectors=True,
    subnetworks=[NetworkAEMORooftop, NetworkAEMORooftopBackfill],
    fueltechs=all_fueltechs_without_rooftop,
)

NetworkWEM = NetworkSchema(
    code="WEM",
    label="WEM",
    country="au",
    timezone="Australia/Perth",
    timezone_database="AWST",
    offset=480,
    interval_size=30,
    interval_size_price=5,
    data_first_seen=datetime.fromisoformat("2006-09-20T02:00:00+08:00"),
    price_first_seen=datetime.fromisoformat("2012-01-07T08:00:00+08:00"),
    # WEM is slower to update at times. set to 4 hours.
    monitor_interval_alert_threshold=60 * 4,
    subnetworks=[NetworkAPVI],
    fueltechs=all_fueltechs_without_rooftop,
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
    subnetworks=[NetworkNEM, NetworkWEM],
)


NETWORKS = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAU, NetworkAEMORooftop, NetworkAEMORooftop]
