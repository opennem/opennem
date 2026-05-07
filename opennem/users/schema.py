from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from opennem.api.schema import APIV4ResponseSchema
from opennem.users.plans import OpenNEMPlan, PlanConfig, get_plan_config
from opennem.utils.dates import chop_datetime_microseconds


class OpenNEMRoles(Enum):
    admin = "admin"
    anonymous = "anonymous"


class OpenNEMUserRateLimit(BaseModel):
    limit: int = Field(
        description="Maximum requests allowed in the current rate-limit window.",
        examples=[60],
    )
    remaining: int = Field(
        description="Requests still available in the current window.",
        examples=[42],
    )
    reset: datetime | int = Field(
        description=(
            "UTC timestamp when the rate-limit window resets. Accepts a unix-millis integer on input; "
            "serialized as ISO-8601 datetime."
        ),
        examples=["2024-09-01T00:01:00Z"],
    )

    # convert reset unix timestamp to datetime in UTC time
    @field_validator("reset", mode="before")
    def reset_utc(cls, v) -> datetime:
        # convert milliseconds to seconds
        dt = chop_datetime_microseconds(datetime.fromtimestamp(v / 1000, tz=UTC))

        if not dt:
            raise ValueError("Invalid reset")

        return dt


class OpennemAPIRequestMeta(BaseModel):
    remaining: int | None = Field(
        default=None,
        description="API credits remaining for the current billing period.",
        examples=[9876],
    )
    reset: datetime | None = Field(
        default=None,
        description="UTC timestamp when the credit balance refreshes.",
        examples=["2024-10-01T00:00:00Z"],
    )


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
    data: OpenNEMUser = Field(..., description="Internal user record (admin-only fields included).")


class OpenNEMUserMe(BaseModel):
    """Public-facing user profile for /v4/me"""

    id: str = Field(
        description="Stable user identifier.",
        examples=["user_2abcDEF12345"],
    )
    full_name: str | None = Field(
        default=None,
        description="User's full name as set in their profile.",
        examples=["Ada Lovelace"],
    )
    email: str | None = Field(
        default=None,
        description="User's primary email address.",
        examples=["ada@example.com"],
    )
    plan: OpenNEMPlan = Field(
        OpenNEMPlan.COMMUNITY,
        description="Subscription plan the user is on.",
        examples=["COMMUNITY"],
    )
    roles: list[OpenNEMRoles] = Field(
        default_factory=list,
        description="Authorization roles attached to this user.",
        examples=[["anonymous"]],
    )
    is_admin: bool | None = Field(
        default=None,
        description="`true` for admin users; absent otherwise.",
        examples=[None],
    )
    rate_limit: OpenNEMUserRateLimit | None = Field(
        default=None,
        description="Current rate-limit window for this user's API key.",
    )
    credits: OpennemAPIRequestMeta | None = Field(
        default=None,
        description="API credit balance metadata.",
    )


class OpenNEMUserMeResponse(APIV4ResponseSchema):
    data: OpenNEMUserMe = Field(..., description="Authenticated user's profile, plan, roles, rate-limit, and credit balance.")


def to_user_me(user: OpenNEMUser) -> OpenNEMUserMe:
    return OpenNEMUserMe(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        plan=user.plan,
        roles=user.roles,
        is_admin=True if user.is_admin else None,
        rate_limit=user.rate_limit,
        credits=user.meta,
    )
