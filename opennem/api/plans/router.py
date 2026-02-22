"""Plans endpoint — serves canonical plan definitions."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from opennem.users.plans import PLAN_CONFIGS, PlanConfig

logger = logging.getLogger("opennem.api.plans")

router = APIRouter()

# Optional bearer — plans endpoint is public but admins see hidden plans
_optional_bearer = HTTPBearer(auto_error=False)


def _is_admin_request(authorization: HTTPAuthorizationCredentials | None) -> bool:
    """Quick check if request has admin auth — full validation happens elsewhere."""
    if not authorization:
        return False
    # Import here to avoid circular imports
    from opennem import settings

    return authorization.credentials == settings.api_dev_key


@router.get(
    "",
    response_model=list[PlanConfig],
    description="Get available plans",
)
async def get_plans(
    authorization: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)] = None,
) -> list[PlanConfig]:
    """Return plan configs. Non-admin users only see visible plans."""
    is_admin = _is_admin_request(authorization)

    if is_admin:
        return list(PLAN_CONFIGS.values())

    return [config for config in PLAN_CONFIGS.values() if config.visible]
