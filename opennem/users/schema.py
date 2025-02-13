from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, field_validator

from opennem.api.schema import APIV4ResponseSchema
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


class OpennemAPIRequestMeta(BaseModel):
    remaining: int | None = None
    reset: datetime | None = None


class OpenNEMUser(BaseModel):
    id: str
    full_name: str | None = None
    email: str | None = None
    owner_id: str | None = None
    plan: str | None = None
    rate_limit: OpenNEMUserRateLimit | None = None
    unkey_meta: dict | None = None
    roles: list[OpenNEMRoles] = [OpenNEMRoles.anonymous]
    meta: OpennemAPIRequestMeta | None = None


class OpenNEMAPIInvite(BaseModel):
    name: str
    api_key: str
    access_level: str
    limit: int
    limit_interval: str
    domain: str = "opennem.org.au"


class OpennemUserResponse(APIV4ResponseSchema):
    data: OpenNEMUser
