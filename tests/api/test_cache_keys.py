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
