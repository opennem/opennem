"""
OpenNEM API Security Module

Handles API key validation (Unkey) and user enrichment (Clerk).
Plan resolution: Clerk privateMetadata.plan → OpenNEMPlan enum.
Admin resolution: Clerk privateMetadata.role == "admin".
"""

import logging
from typing import Annotated

from clerk_backend_api import Clerk
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from opennem import settings
from opennem.clients.unkey import unkey_validate
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

logger = logging.getLogger("opennem.api.security")

# Initialize clients
if not settings.unkey_root_key or not settings.clerk_secret_key:
    raise ValueError("No API key or clerk secret key set")

clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)

# Bearer token scheme
api_token_scheme = HTTPBearer()

# Default internal user for development
_OPENNEM_INTERNAL_USER = OpenNEMUser(
    id="dev",
    owner_id="dev",
    plan=OpenNEMPlan.ENTERPRISE,
    roles=[OpenNEMRoles.admin, OpenNEMRoles.anonymous],
)


def _resolve_plan(private_metadata: dict | None, unkey_meta: dict | None = None) -> OpenNEMPlan:
    """Resolve plan from Clerk privateMetadata, falling back to Unkey key meta, then COMMUNITY."""
    # Try Clerk first
    if private_metadata:
        raw = private_metadata.get("plan")
        if raw:
            try:
                return OpenNEMPlan(raw)
            except ValueError:
                # Legacy "BASIC" → COMMUNITY
                if raw == "BASIC":
                    return OpenNEMPlan.COMMUNITY
                logger.warning(f"Unknown plan code from Clerk: {raw}, defaulting to COMMUNITY")

    # Fallback to Unkey key metadata
    if unkey_meta and "plan" in unkey_meta:
        try:
            return OpenNEMPlan(unkey_meta["plan"])
        except ValueError:
            pass

    return OpenNEMPlan.COMMUNITY


def _resolve_admin(private_metadata: dict | None) -> bool:
    """Check if user has admin role in Clerk privateMetadata."""
    if private_metadata:
        return private_metadata.get("role") == "admin"
    return False


async def get_current_user(
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(api_token_scheme)], with_clerk: bool = True
) -> OpenNEMUser:
    """FastAPI dependency: validate API key, resolve plan + roles from Clerk."""
    try:
        key = authorization.credentials

        if not key or len(key) < 10:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        # Dev key bypass
        if key == settings.api_dev_key:
            return _OPENNEM_INTERNAL_USER

        # Validate with Unkey
        user = await unkey_validate(api_key=key)

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        if not with_clerk:
            return user

        # Enrich with Clerk user data
        if not user.owner_id:
            logger.info(f"No owner_id for user {user.id}, skipping Clerk enrichment")
            # Resolve plan from unkey meta if available
            user.plan = _resolve_plan(None, user.unkey_meta)
            return user

        clerk_user = await clerk_client.users.get_async(user_id=user.owner_id)

        if not clerk_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        user.full_name = f"{clerk_user.first_name} {clerk_user.last_name}"
        user.email = clerk_user.email_addresses[0].email_address

        private_meta = clerk_user.private_metadata if clerk_user.private_metadata else None

        # Resolve plan from Clerk, with Unkey meta fallback
        user.plan = _resolve_plan(private_meta, user.unkey_meta)

        # Resolve admin from Clerk privateMetadata.role
        if _resolve_admin(private_meta):
            if OpenNEMRoles.admin not in user.roles:
                user.roles.append(OpenNEMRoles.admin)

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from e


def check_roles(required_roles: list[OpenNEMRoles]):
    """Creates a dependency that checks if user has any of the required roles."""

    async def role_checker(current_user: Annotated[OpenNEMUser, Depends(get_current_user)]) -> OpenNEMUser:
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


# Common auth dependencies
authenticated_user = Annotated[OpenNEMUser, Depends(get_current_user)]
admin_user = Annotated[OpenNEMUser, Depends(check_roles([OpenNEMRoles.admin]))]
