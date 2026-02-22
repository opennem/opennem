from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, field_validator

from opennem.api.schema import APIV4ResponseSchema
from opennem.users.plans import OpenNEMPlan, PlanConfig, get_plan_config
from opennem.utils.dates import chop_datetime_microseconds


class OpenNEMRoles(Enum):
    admin = "admin"
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
    plan: OpenNEMPlan = OpenNEMPlan.COMMUNITY
    rate_limit: OpenNEMUserRateLimit | None = None
    unkey_meta: dict | None = None
    roles: list[OpenNEMRoles] = [OpenNEMRoles.anonymous]
    meta: OpennemAPIRequestMeta | None = None

    @property
    def is_admin(self) -> bool:
        return OpenNEMRoles.admin in self.roles

    def has_role(self, role: OpenNEMRoles) -> bool:
        return role in self.roles

    @property
    def plan_config(self) -> PlanConfig:
        return get_plan_config(self.plan)


class OpennemUserResponse(APIV4ResponseSchema):
    data: OpenNEMUser
