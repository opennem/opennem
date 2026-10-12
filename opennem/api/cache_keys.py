"""
Shared response-cache key builder for API endpoints.

The fastapi-cache default builder hashes every kwarg, including the ClickHouse client and the
`user` repr (rate-limit / meta change per request), so keys were per-user, per-process and
per-request. This builder drops both and keys on the plan tier instead: date-range limits are
validated inside the handlers per tier, so tiers must never share an entry.
"""

import hashlib
from collections.abc import Callable
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from opennem.users.schema import OpenNEMUser

# kwargs that never influence the response body
_EXCLUDED_KWARGS = frozenset({"client", "user"})


def user_tier(user: OpenNEMUser | None) -> str:
    """Cache-relevant identity of a user: plan tier and admin flag only."""
    if user is None:
        return "anon"
    return f"{user.plan.value if hasattr(user.plan, 'value') else user.plan}:{'admin' if user.is_admin else 'user'}"


def tiered_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    request: Request | None = None,
    response: Response | None = None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """Key on endpoint + request params + user tier; ignore client and per-request user state."""
    params = sorted((k, repr(v)) for k, v in kwargs.items() if k not in _EXCLUDED_KWARGS)
    tier = user_tier(kwargs.get("user"))
    raw = f"{func.__module__}:{func.__name__}:{args}:{params}:{tier}"
    return f"{namespace}:{hashlib.md5(raw.encode()).hexdigest()}"  # noqa: S324
