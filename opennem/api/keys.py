from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Callable, Coroutine
from typing import Annotated, Any, TypeVar

from clerk_backend_api import Clerk
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from unkey.py import models

from opennem import settings
from opennem.clients.unkey import UnkeyInvalidUserException, unkey_validate
from opennem.users.plans import OpenNEMPlan
from opennem.users.schema import OpenNEMRoles, OpenNEMUser

logger = logging.getLogger("opennem.api.keys")

__all__ = ("api_protected",)

T = TypeVar("T")
CallableT = Callable[..., T]
CallbackT = CallableT[Any]
DecoratorT = CallableT[CallbackT]
ExtractorT = Callable[[tuple[Any], dict[str, Any]], str | None]


InvalidKeyHandlerT = Callable[[dict[str, Any], models.V2KeysVerifyKeyResponseBody | None], Any]
"""The type of a callback used to handle cases where the key was invalid."""

ExcHandlerT = Callable[[Exception], Any]
"""The type of a callback used to handle exceptions during verification."""

# API Keys
if not settings.unkey_root_key or not settings.clerk_secret_key:
    raise ValueError("No API key or clerk secret key set")

clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)

api_token_scheme = HTTPBearer()

ApiAuthorization = Annotated[HTTPAuthorizationCredentials, Depends(api_token_scheme)]


def api_protected(
    roles: list[OpenNEMRoles] | None = None,
    on_invalid_key: InvalidKeyHandlerT | None = None,
    on_exc: ExcHandlerT | None = None,
) -> DecoratorT:
    """
    Decorator to protect API endpoints.

    This decorator validates API keys and attaches the user to the request.
    It also checks for specific roles if provided.
    """
    if not settings.unkey_api_id:
        raise ValueError("No API ID set")

    def _on_exc(exc: Exception) -> Any:
        if on_exc:
            return on_exc(exc)

        raise exc

    def _key_extractor(*args: Any, **kwargs: Any) -> str | None:
        """Extracts the API key from the request as a bearer token"""
        if isinstance(auth := kwargs.get("authorization", None), HTTPAuthorizationCredentials):
            return auth.credentials

        return None

    def wrapper(
        func: CallableT[T],
    ) -> CallableT[Coroutine[Any, Any, OpenNEMUser]]:
        @functools.wraps(func)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            try:
                if not (key := _key_extractor(*args, **kwargs)):
                    message = "Failed to get API key"
                    logger.error(message)
                    raise HTTPException(status_code=403, detail=message)

                # dev hard coded internalkey bypasses unkey
                if not key or not len(key) > 10:
                    logger.error(f"Failed to get API key: {key}")
                    raise HTTPException(status_code=403, detail="Permission denied: no key provided")

                # dev key bypasses unkey
                if key == settings.api_dev_key:
                    user = OpenNEMUser(
                        id="dev",
                        owner_id="dev",
                        plan=OpenNEMPlan.ENTERPRISE,
                        roles=[OpenNEMRoles.admin, OpenNEMRoles.anonymous],
                    )

                    if "user" in inspect.signature(func).parameters:
                        kwargs["user"] = user

                    # if the function is a coroutine, call it as a coroutine
                    if inspect.iscoroutinefunction(func):
                        value = await func(*args, **kwargs)
                    else:
                        value = func(*args, **kwargs)
                    return value

                # try unkey verification of the API key in bearer
                unkey_verification = None

                try:
                    unkey_verification = await unkey_validate(api_key=key)
                except UnkeyInvalidUserException as e:
                    raise HTTPException(status_code=403, detail=str(e)) from e

                if not unkey_verification:
                    logger.error(f"Unkey verification failed for key: {key}")
                    raise HTTPException(status_code=403, detail="Permission denied")

                user = unkey_verification

                # Attach Clerk user data if key has owner association
                if user.owner_id:
                    clerk_user = await clerk_client.users.get_async(user_id=user.owner_id)

                    if not clerk_user:
                        logger.error(f"Clerk user not found for {user.owner_id}")
                        raise HTTPException(status_code=403, detail="Permission denied")

                    user.full_name = clerk_user.first_name + " " + clerk_user.last_name
                    user.email = clerk_user.email_addresses[0].email_address

                    # Resolve plan from Clerk privateMetadata
                    raw_plan = clerk_user.private_metadata.get("plan") if clerk_user.private_metadata else None
                    if raw_plan:
                        try:
                            user.plan = OpenNEMPlan(raw_plan if raw_plan != "BASIC" else "COMMUNITY")
                        except ValueError:
                            user.plan = OpenNEMPlan.COMMUNITY
                    else:
                        user.plan = OpenNEMPlan.COMMUNITY

                    # Resolve admin from Clerk privateMetadata.role
                    if clerk_user.private_metadata and clerk_user.private_metadata.get("role") == "admin":
                        if OpenNEMRoles.admin not in user.roles:
                            user.roles.append(OpenNEMRoles.admin)
                else:
                    logger.info(f"Key {user.id} not associated with Clerk user, skipping enrichment")
                    user.full_name = None
                    user.email = None

                if "user" in inspect.signature(func).parameters:
                    kwargs["user"] = user

                if roles:
                    if not any(r in user.roles for r in roles):
                        raise HTTPException(status_code=403, detail="Permission denied")

                if inspect.iscoroutinefunction(func):
                    value = await func(*args, **kwargs)
                else:
                    value = func(*args, **kwargs)

            except Exception as exc:
                return _on_exc(exc)

            return value

        return inner

    return wrapper
