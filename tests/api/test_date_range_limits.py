"""Unit tests for data-range limit enforcement (opennem.api.data.utils).

This is the symptom side of #555: the internal/enterprise key must be able to
pull the full archive (e.g. ``interval=1M`` from 2000-01-01), while anonymous /
COMMUNITY callers stay capped at 732 days. These tests pin ``get_max_interval_days``
and ``validate_date_range`` so the cap can't silently regress for higher tiers.
"""

from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from opennem.api.data.utils import get_max_interval_days, validate_date_range
from opennem.core.time_interval import Interval
from opennem.schema.network import NetworkNEM
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

# Full-archive window from the #555 report (2000-01-01 → a fixed recent date).
_ARCHIVE_START = datetime(2000, 1, 1)
_ARCHIVE_END = datetime(2026, 6, 9)

_COMMUNITY = OpenNEMUser(id="community", plan=OpenNEMPlan.COMMUNITY, roles=[OpenNEMRoles.anonymous])
_ENTERPRISE = OpenNEMUser(id="enterprise", plan=OpenNEMPlan.ENTERPRISE, roles=[OpenNEMRoles.anonymous])
# admin role must lift limits regardless of the plan attached to the key
_ADMIN = OpenNEMUser(id="admin", plan=OpenNEMPlan.COMMUNITY, roles=[OpenNEMRoles.admin, OpenNEMRoles.anonymous])


# --- get_max_interval_days -------------------------------------------------


@pytest.mark.parametrize(
    ["user", "expected"],
    [
        (None, 732),  # anonymous → COMMUNITY bucket
        (_COMMUNITY, 732),
        (_ENTERPRISE, 36500),
        (_ADMIN, 36500),  # admin role wins even on a COMMUNITY plan
    ],
)
def test_max_interval_days_month(user: OpenNEMUser | None, expected: int) -> None:
    assert get_max_interval_days(Interval.MONTH, user) == expected


def test_max_interval_days_interval_tiers() -> None:
    """5-minute interval: COMMUNITY is tightly capped, admin/enterprise far higher."""
    assert get_max_interval_days(Interval.INTERVAL, None) == 8
    assert get_max_interval_days(Interval.INTERVAL, _ENTERPRISE) == 30
    assert get_max_interval_days(Interval.INTERVAL, _ADMIN) == 30


# --- validate_date_range: the #555 range cap -------------------------------


@pytest.mark.parametrize("user", [None, _COMMUNITY])
def test_full_archive_rejected_for_anonymous_and_community(user: OpenNEMUser | None) -> None:
    """2000→now at 1M exceeds the 732-day COMMUNITY cap → 400."""
    with pytest.raises(HTTPException) as exc:
        validate_date_range(
            network=NetworkNEM,
            interval=Interval.MONTH,
            user=user,
            date_start=_ARCHIVE_START,
            date_end=_ARCHIVE_END,
        )
    assert exc.value.status_code == 400
    assert "Maximum range is 732 days" in exc.value.detail


@pytest.mark.parametrize("user", [_ENTERPRISE, _ADMIN])
def test_full_archive_allowed_for_enterprise_and_admin(user: OpenNEMUser) -> None:
    """The #555 fix: enterprise/admin pull the full archive at 1M without a cap."""
    start, end = validate_date_range(
        network=NetworkNEM,
        interval=Interval.MONTH,
        user=user,
        date_start=_ARCHIVE_START,
        date_end=_ARCHIVE_END,
    )
    assert (start, end) == (_ARCHIVE_START, _ARCHIVE_END)


# --- validate_date_range: the period (how-far-back) limit ------------------


def test_period_limit_blocks_community_far_past() -> None:
    """COMMUNITY (period_limit_days=730) can't start a window outside the last ~2y,
    even when the window itself is within the range cap."""
    far_start = datetime.now() - timedelta(days=900)
    with pytest.raises(HTTPException) as exc:
        validate_date_range(
            network=NetworkNEM,
            interval=Interval.MONTH,
            user=_COMMUNITY,
            date_start=far_start,
            date_end=far_start + timedelta(days=30),
        )
    assert exc.value.status_code == 400
    assert "too far in the past" in exc.value.detail


@pytest.mark.parametrize("user", [_ENTERPRISE, _ADMIN])
def test_period_limit_bypassed_for_enterprise_and_admin(user: OpenNEMUser) -> None:
    """ENTERPRISE (period_limit_days=-1) and admin ignore the how-far-back limit."""
    far_start = datetime.now() - timedelta(days=900)
    start, end = validate_date_range(
        network=NetworkNEM,
        interval=Interval.MONTH,
        user=user,
        date_start=far_start,
        date_end=far_start + timedelta(days=30),
    )
    assert start == far_start


def test_tz_aware_dates_rejected() -> None:
    """Dates must be network-local naive; a tz-aware date is a 400."""
    from datetime import UTC

    with pytest.raises(HTTPException) as exc:
        validate_date_range(
            network=NetworkNEM,
            interval=Interval.MONTH,
            user=_ENTERPRISE,
            date_start=_ARCHIVE_START.replace(tzinfo=UTC),
            date_end=_ARCHIVE_END,
        )
    assert exc.value.status_code == 400
    assert "timezone naive" in exc.value.detail
