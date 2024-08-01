from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import unkey
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from unkey import models

from opennem import settings
from opennem.clients.unkey import OpenNEMUser, unkey_validate
from opennem.users.schema import OpenNEMRoles

logger = logging.getLogger("opennem.api.keys")

__all__ = ("api_protected",)

T = TypeVar("T")
CallableT = Callable[..., T]
CallbackT = CallableT[Any]
DecoratorT = CallableT[CallbackT]
ExtractorT = Callable[[tuple[Any], dict[str, Any]], str | None]


InvalidKeyHandlerT = Callable[[dict[str, Any], models.ApiKeyVerification | None], Any]
"""The type of a callback used to handle cases where the key was invalid."""

ExcHandlerT = Callable[[Exception], Any]
"""The type of a callback used to handle exceptions during verification."""

# API Keys
unkey_client = unkey.Client(api_key=settings.unkey_root_key)

api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    if not settings.unkey_api_id:
        raise HTTPException(status_code=403, detail="Invalid API key")

    result = await unkey_client.keys.verify_key(api_key, settings.unkey_api_id)
    if not result.is_ok or not result.unwrap().valid:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return result.unwrap()


def api_protected(
    roles: list[OpenNEMRoles] | None = None,
    on_invalid_key: InvalidKeyHandlerT | None = None,
    on_exc: ExcHandlerT | None = None,
) -> DecoratorT:
    """ """

    if not settings.unkey_api_id:
        raise ValueError("No API ID set")

    def _on_invalid_key(data: dict[str, Any], verification: models.ApiKeyVerification | None = None) -> Any:
        if on_invalid_key:
            return on_invalid_key(data, verification)

        return data

    def _on_exc(exc: Exception) -> Any:
        if on_exc:
            return on_exc(exc)

        raise exc

    def _key_extractor(*args: Any, **kwargs: Any) -> str | None:
        if isinstance(auth := kwargs.get("authorization"), str):
            return auth.split(" ")[-1]

        return None

    def wrapper(
        func: CallableT[T],
    ) -> CallableT[Coroutine[Any, Any, OpenNEMUser]]:
        @functools.wraps(func)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            try:
                if not (key := _key_extractor(*args, **kwargs)):
                    message = "Failed to get API key"
                    raise HTTPException(status_code=403, detail=message)

                # dev key bypasses unkey
                if key == settings.api_dev_key:
                    verification = OpenNEMUser(
                        valid=True,
                        id="dev",
                        owner_id="dev",
                        roles=[OpenNEMRoles.admin, OpenNEMRoles.user, OpenNEMRoles.anonymous],
                    )
                    kwargs["user"] = verification
                    if inspect.iscoroutinefunction(func):
                        value = await func(*args, **kwargs)
                    else:
                        value = func(*args, **kwargs)
                    return value

                verification = await unkey_validate(api_key=key)

                if not verification:
                    raise HTTPException(status_code=403, detail="Permission denied")

                kwargs["user"] = verification

                if roles:
                    if not any(r in verification.roles for r in roles):
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
