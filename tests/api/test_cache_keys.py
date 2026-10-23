"""Key builder unit tests: user/client are dropped, plan tier is kept."""

from typing import Any

from opennem.api.cache_keys import tiered_key_builder
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit


def _fn() -> None: ...


def _user(uid: str = "u1", plan: OpenNEMPlan = OpenNEMPlan.COMMUNITY, admin: bool = False, remaining: int = 10) -> OpenNEMUser:
    return OpenNEMUser(
        id=uid,
        plan=plan,
        roles=[OpenNEMRoles.admin] if admin else [OpenNEMRoles.anonymous],
        rate_limit=OpenNEMUserRateLimit(limit=60, remaining=remaining, reset=1_700_000_000_000),
    )


def _key(**kwargs: Any) -> str:
    return tiered_key_builder(_fn, "ns", args=(), kwargs=kwargs)


def test_different_users_same_tier_share_key() -> None:
    a = _key(network_code="NEM", client=object(), user=_user("a", remaining=1))
    b = _key(network_code="NEM", client=object(), user=_user("b", remaining=59))
    assert a == b


def test_different_client_instances_share_key() -> None:
    assert _key(network_code="NEM", client=object()) == _key(network_code="NEM", client=object())


def test_different_tier_different_key() -> None:
    community = _key(network_code="NEM", user=_user(plan=OpenNEMPlan.COMMUNITY))
    pro = _key(network_code="NEM", user=_user(plan=OpenNEMPlan.PRO))
    assert community != pro


def test_admin_differs_from_same_plan_non_admin() -> None:
    assert _key(user=_user(admin=True)) != _key(user=_user(admin=False))


def test_anonymous_differs_from_authed() -> None:
    assert _key(user=None) != _key(user=_user())
    assert _key() == _key(user=None)


def test_kwarg_order_stable() -> None:
    assert _key(a=1, b=[2, 3]) == _key(b=[2, 3], a=1)


def test_params_change_key() -> None:
    assert _key(network_code="NEM") != _key(network_code="WEM")
    assert _key(date_start="2026-01-01") != _key(date_start="2026-01-02")


# --- date window normalisation (#729) ---

from datetime import datetime  # noqa: E402

from opennem.core.metric import Metric  # noqa: E402
from opennem.core.time_interval import Interval  # noqa: E402


def _win(start: str, end: str | None, interval: Interval = Interval.INTERVAL, **kw: Any) -> str:
    return _key(
        network_code="NEM",
        interval=interval,
        date_start=datetime.fromisoformat(start),
        date_end=datetime.fromisoformat(end) if end else None,
        **kw,
    )


def test_same_5m_grid_window_shares_key() -> None:
    a = _win("2026-10-17T06:15:30", "2026-10-24T06:15:30")
    b = _win("2026-10-17T06:15:50", "2026-10-24T06:15:50")
    assert a == b


def test_all_sub_day_intervals_normalise() -> None:
    for itv in (Interval.INTERVAL, Interval.HALF_HOUR, Interval.HOUR):
        assert _win("2026-10-17T06:15:30", "2026-10-24T06:15:30", itv) == _win("2026-10-17T06:15:31", "2026-10-24T06:15:59", itv)


def test_different_grid_window_differs() -> None:
    assert _win("2026-10-17T06:15:30", "2026-10-24T06:15:30") != _win("2026-10-17T06:15:30", "2026-10-24T06:20:30")
    assert _win("2026-10-17T06:15:30", "2026-10-24T06:15:30") != _win("2026-10-17T06:20:30", "2026-10-24T06:15:30")


def test_exact_grid_point_not_merged_with_next() -> None:
    # 06:20:00 includes the 06:20 row in a start bound; 06:20:01 does not
    assert _win("2026-10-17T06:20:00", "2026-10-24T06:20:00") != _win("2026-10-17T06:20:01", "2026-10-24T06:20:00")


def test_day_and_coarser_intervals_stay_exact() -> None:
    for itv in (Interval.DAY, Interval.WEEK, Interval.MONTH, Interval.YEAR):
        assert _win("2026-10-17T06:15:30", "2026-10-24T06:15:30", itv) != _win("2026-10-17T06:15:31", "2026-10-24T06:15:30", itv)


def test_live_date_end_none_unchanged() -> None:
    assert _win("2026-10-17T06:15:30", None) != _win("2026-10-17T06:15:31", None)
    assert _win("2026-10-17T06:15:30", None) == _win("2026-10-17T06:15:30", None)


def test_date_start_none_unchanged() -> None:
    def k(end: str) -> str:
        return _key(interval=Interval.INTERVAL, date_start=None, date_end=datetime.fromisoformat(end))

    assert k("2026-10-24T06:15:30") != k("2026-10-24T06:15:31")


def test_range_days_still_distinguishes() -> None:
    # same grid points but raw range crosses an integer-day boundary (plan limit check uses .days)
    assert _win("2026-10-17T06:15:30", "2026-10-24T06:15:30") != _win("2026-10-17T06:15:31", "2026-10-24T06:15:30")


def test_forecast_metrics_stay_exact() -> None:
    m = [Metric.SOLAR_ROOFTOP_FORECAST]
    assert _win("2026-10-17T06:15:30", "2026-10-24T06:15:30", metrics=m) != _win(
        "2026-10-17T06:15:31", "2026-10-24T06:15:30", metrics=m
    )


def test_normalisation_keeps_tier_and_other_params() -> None:
    a = _win("2026-10-17T06:15:30", "2026-10-24T06:15:30", user=_user(plan=OpenNEMPlan.COMMUNITY))
    b = _win("2026-10-17T06:15:31", "2026-10-24T06:15:59", user=_user(plan=OpenNEMPlan.PRO))
    assert a != b
    assert _win("2026-10-17T06:15:30", "2026-10-24T06:15:30", network_region="NSW1") != _win(
        "2026-10-17T06:15:30", "2026-10-24T06:15:30", network_region="VIC1"
    )
