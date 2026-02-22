"""unkey client for validating api keys"""

import asyncio
import logging
from functools import wraps

from cachetools import TTLCache
from pydantic import ValidationError
from unkey.py import Unkey

from opennem import settings
from opennem.users.schema import OpennemAPIRequestMeta, OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit

logger = logging.getLogger("opennem.clients.unkey")

# Cache for unkey validation results - 5 minute TTL
_unkey_cache = TTLCache(maxsize=10000, ttl=60 * 5)


def cache_unkey_result(func):
    """Decorator to cache unkey validation results for 5 minutes."""

    @wraps(func)
    async def wrapper(api_key: str, *args, **kwargs) -> OpenNEMUser | None:
        # Check cache first
        if api_key in _unkey_cache:
            return _unkey_cache[api_key]

        # Call original function
        result = await func(api_key, *args, **kwargs)

        # Cache successful results
        if result:
            _unkey_cache[api_key] = result

        return result

    return wrapper


class UnkeyInvalidUserException(Exception):
    pass


@cache_unkey_result
async def unkey_validate(api_key: str) -> None | OpenNEMUser:
    """
    Validate a key with unkey.
    Results are cached for 5 minutes to reduce API calls.
    """

    if not settings.unkey_root_key:
        raise Exception("No unkey root key set")

    try:
        async with Unkey(root_key=settings.unkey_root_key) as client:
            response = await client.keys.verify_key_async(key=api_key)

        if not response or not response.data:
            logger.warning("Unkey verification failed: no response data")
            raise UnkeyInvalidUserException("Verification failed: no response")

        data = response.data

        if not data.valid:
            logger.info("API key is not valid")
            raise UnkeyInvalidUserException("Verification failed: not valid")

        if not data.key_id:
            logger.info("API key id is not valid no id")
            raise UnkeyInvalidUserException("Verification failed: no id")

        try:
            # Extract owner_id from identity if available
            owner_id = data.identity.external_id if data.identity else None
            logger.debug(f"Unkey response - identity: {data.identity}, owner_id extracted: {owner_id}")

            model = OpenNEMUser(
                id=data.key_id,
                owner_id=owner_id,
                unkey_meta=data.meta,
            )

            # Set meta with credits and expiry
            model.meta = OpennemAPIRequestMeta(remaining=data.credits if data.credits else None, reset=data.expires)

            # Process ratelimits array
            if data.ratelimits and len(data.ratelimits) > 0:
                first_ratelimit = data.ratelimits[0]
                model.rate_limit = OpenNEMUserRateLimit(
                    limit=first_ratelimit.limit, remaining=first_ratelimit.remaining, reset=first_ratelimit.reset
                )

            # Resolve roles from unkey meta (admin only)
            if data.meta and "roles" in data.meta:
                for role in data.meta["roles"]:
                    try:
                        model.roles.append(OpenNEMRoles(role))
                    except ValueError:
                        # Skip unknown roles (legacy pro/academic/user)
                        pass

            return model
        except ValidationError as ve:
            logger.error(f"Pydantic validation error: {ve}")
            for error in ve.errors():
                logger.error(f"Field: {error['loc'][0]}, Error: {error['msg']}")
            raise UnkeyInvalidUserException("Unkey verification failed: model validation error") from ve

    except UnkeyInvalidUserException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in unkey_validate: {e}")
        raise UnkeyInvalidUserException("Unkey verification failed: unexpected error") from e


# debug entry point
if __name__ == "__main__":
    import os

    test_key = os.environ.get("OPENNEM_UNKEY_TEST_KEY", None)

    if not test_key:
        raise Exception("No test key set")

    model = asyncio.run(unkey_validate(api_key=test_key))

    if not model:
        print("No model")
    else:
        print(model)
