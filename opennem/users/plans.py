"""Canonical plan definitions for OpenNEM/OpenElectricity.

API is the single source of truth for plan config.
Clerk privateMetadata.plan is the source of truth for a user's current plan.
"""

from enum import Enum

from pydantic import BaseModel

from opennem.core.time_interval import Interval


class OpenNEMPlan(str, Enum):
    COMMUNITY = "COMMUNITY"
    PRO = "PRO"
    ACADEMIC = "ACADEMIC"
    ENTERPRISE = "ENTERPRISE"


class PlanConfig(BaseModel):
    code: OpenNEMPlan
    name: str
    description: str
    price: str
    daily_credits: int
    burst_rate_limit: str
    key_limit: int
    bucket_limits: dict[str, int]
    period_limit_days: int
    historical_data: str
    features: list[str]
    visible: bool = True
    cta: str | None = None


BUCKET_LIMITS_USER: dict[Interval, int] = {
    Interval.INTERVAL: 8,
    Interval.HOUR: 32,
    Interval.DAY: 366,
    Interval.WEEK: 366,
    Interval.MONTH: 732,
    Interval.QUARTER: 1830,
    Interval.SEASON: 1830,
    Interval.YEAR: 3700,
}

BUCKET_LIMITS_ADMIN: dict[Interval, int] = {
    Interval.INTERVAL: 30,
    Interval.HOUR: 365,
    Interval.DAY: 3650,
    Interval.WEEK: 3650,
    Interval.MONTH: 10000,
    Interval.QUARTER: 10000,
    Interval.SEASON: 10000,
    Interval.YEAR: 10000,
}

# Concrete plan values
COMMUNITY_CREDITS = 500
PRO_CREDITS = 5_000
ACADEMIC_CREDITS = 2_000
ENTERPRISE_CREDITS = -1  # unlimited

PLAN_CONFIGS: dict[OpenNEMPlan, PlanConfig] = {
    OpenNEMPlan.COMMUNITY: PlanConfig(
        code=OpenNEMPlan.COMMUNITY,
        name="Community",
        description="For hobbyists and initial experiments",
        price="Free",
        daily_credits=COMMUNITY_CREDITS,
        burst_rate_limit="2/s",
        key_limit=1,
        bucket_limits={k.value: v for k, v in BUCKET_LIMITS_USER.items()},
        period_limit_days=367,
        historical_data="1 year",
        features=["Community support"],
        visible=True,
        cta="upgrade",
    ),
    OpenNEMPlan.PRO: PlanConfig(
        code=OpenNEMPlan.PRO,
        name="Pro",
        description="For professionals and power users",
        price="$49/mo",
        daily_credits=PRO_CREDITS,
        burst_rate_limit="5/s",
        key_limit=10,
        bucket_limits={k.value: v for k, v in BUCKET_LIMITS_ADMIN.items()},
        period_limit_days=-1,
        historical_data="Full",
        features=["Priority email support"],
        visible=False,  # not ready yet
    ),
    OpenNEMPlan.ACADEMIC: PlanConfig(
        code=OpenNEMPlan.ACADEMIC,
        name="Academic",
        description="For researchers and students at accredited institutions",
        price="Free",
        daily_credits=ACADEMIC_CREDITS,
        burst_rate_limit="2/s",
        key_limit=5,
        bucket_limits={k.value: v for k, v in BUCKET_LIMITS_ADMIN.items()},
        period_limit_days=-1,
        historical_data="Full",
        features=["Community support"],
        visible=True,
        cta="academic",
    ),
    OpenNEMPlan.ENTERPRISE: PlanConfig(
        code=OpenNEMPlan.ENTERPRISE,
        name="Enterprise",
        description="For organisations that need full access and support",
        price="Custom",
        daily_credits=ENTERPRISE_CREDITS,
        burst_rate_limit="10/s",
        key_limit=-1,  # unlimited
        bucket_limits={k.value: v for k, v in BUCKET_LIMITS_ADMIN.items()},
        period_limit_days=-1,
        historical_data="Full",
        features=["Priority email support"],
        visible=True,
        cta="contact",
    ),
}


def get_plan_config(plan: OpenNEMPlan) -> PlanConfig:
    return PLAN_CONFIGS[plan]


def get_max_interval_days_for_plan(plan: OpenNEMPlan, interval: Interval) -> int:
    config = PLAN_CONFIGS[plan]
    return config.bucket_limits.get(interval.value, 7)
