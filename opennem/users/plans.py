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
    max_days_5m: int
    max_days_1h: int
    max_days_1d: int
    historical_data: str
    features: list[str]
    visible: bool = True
    cta: str | None = None


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
        max_days_5m=8,
        max_days_1h=32,
        max_days_1d=366,
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
        max_days_5m=30,
        max_days_1h=365,
        max_days_1d=3_650,
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
        max_days_5m=30,
        max_days_1h=365,
        max_days_1d=3_650,
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
        max_days_5m=30,
        max_days_1h=365,
        max_days_1d=10_000,
        historical_data="Full",
        features=["Priority email support", "SLA guarantee"],
        visible=True,
        cta="contact",
    ),
}

# Admin limits — orthogonal to plan, grants max across all tiers
ADMIN_MAX_DAYS = {
    Interval.INTERVAL: 30,
    Interval.HOUR: 365,
    Interval.DAY: 10_000,
    Interval.WEEK: 10_000,
    Interval.MONTH: 10_000,
    Interval.QUARTER: 10_000,
    Interval.SEASON: 10_000,
    Interval.YEAR: 10_000,
}

# Map plan max_days fields to Interval enum
_PLAN_INTERVAL_MAP = {
    Interval.INTERVAL: "max_days_5m",
    Interval.HOUR: "max_days_1h",
    Interval.DAY: "max_days_1d",
    Interval.WEEK: "max_days_1d",
    Interval.MONTH: "max_days_1d",
    Interval.QUARTER: "max_days_1d",
    Interval.SEASON: "max_days_1d",
    Interval.YEAR: "max_days_1d",
}


def get_plan_config(plan: OpenNEMPlan) -> PlanConfig:
    return PLAN_CONFIGS[plan]


def get_max_interval_days_for_plan(plan: OpenNEMPlan, interval: Interval) -> int:
    config = PLAN_CONFIGS[plan]
    field = _PLAN_INTERVAL_MAP.get(interval, "max_days_1d")
    return getattr(config, field)
