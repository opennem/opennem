from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from opennem.utils.dates import chop_datetime_microseconds


class OpenNEMRoles(Enum):
    admin = "admin"
    pro = "pro"
    acedemic = "academic"
    user = "user"
    anonymous = "anonymous"


class OpenNEMUserRateLimit(BaseModel):
    limit: int
    remaining: int
    reset: datetime | int

    # convert reset unix timestamp to datetime in UTC time
    @field_validator("reset", mode="before")
    def reset_utc(cls, v) -> datetime:
        # convert milliseconds to seconds
        dt = chop_datetime_microseconds(datetime.fromtimestamp(v / 1000, tz=UTC))

        if not dt:
            raise ValueError("Invalid reset")

        return dt


class OpenNEMUser(BaseModel):
    valid: bool
    id: str
    owner_id: str | None = None
    meta: dict | None = Field(exclude=True, default={})
    error: str | None = None
    rate_limit: OpenNEMUserRateLimit | None = None
    roles: list[OpenNEMRoles] = [OpenNEMRoles.anonymous]


class OpenNEMAPIInvite(BaseModel):
    name: str
    api_key: str
    access_level: str
    limit: int
    limit_interval: str
    domain: str = "opennem.org.au"
