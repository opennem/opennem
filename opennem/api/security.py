"""
OpenNEM API Security Module

This module provides FastAPI dependencies for authentication and authorization.
It handles API key validation using Unkey and user validation using Clerk.
"""

import logging
from typing import Annotated

from clerk_backend_api import Clerk
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from opennem import settings
from opennem.clients.unkey import unkey_validate
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
    roles=[OpenNEMRoles.admin, OpenNEMRoles.user, OpenNEMRoles.anonymous],
)


async def get_current_user(
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(api_token_scheme)], with_clerk: bool = True
) -> OpenNEMUser:
    """
    FastAPI dependency that validates the API key and returns the current user.

    Args:
        authorization: The bearer token credentials from the request

    Returns:
        OpenNEMUser: The validated user object

    Raises:
        HTTPException: If authentication fails
    """
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
        logger.debug(f"Fetching Clerk user for owner_id: {user.owner_id}")

        if not user.owner_id:
            logger.info(f"No owner_id for user {user.id} (key not associated with Clerk user), skipping Clerk enrichment")
            # Set safe defaults for keys without Clerk association
            user.full_name = None
            user.email = None
            user.plan = None
            return user

        clerk_user = await clerk_client.users.get_async(user_id=user.owner_id)

        if not clerk_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        user.full_name = f"{clerk_user.first_name} {clerk_user.last_name}"
        user.email = clerk_user.email_addresses[0].email_address
        user.plan = clerk_user.private_metadata.get("plan") if clerk_user.private_metadata else None

        return user

    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed") from e


def check_roles(required_roles: list[OpenNEMRoles]):
    """
    Creates a FastAPI dependency that checks if the current user has any of the required roles.

    Args:
        required_roles: List of roles that are allowed to access the endpoint

    Returns:
        Dependency function that validates the user's roles
    """

    async def role_checker(current_user: Annotated[OpenNEMUser, Depends(get_current_user)]) -> OpenNEMUser:
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


# Common auth dependencies
authenticated_user = Annotated[OpenNEMUser, Depends(get_current_user)]
admin_user = Annotated[OpenNEMUser, Depends(check_roles([OpenNEMRoles.admin]))]
pro_user = Annotated[OpenNEMUser, Depends(check_roles([OpenNEMRoles.pro, OpenNEMRoles.admin]))]
