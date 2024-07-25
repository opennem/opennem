"""unkney client for validating api keys"""

import asyncio
import logging

import unkey
from pydantic import ValidationError
from unkey import ApiKey, ErrorCode

from opennem import settings
from opennem.users.ratelimit import OPENNEM_RATELIMIT_ADMIN, OPENNEM_RATELIMIT_PRO, OPENNEM_RATELIMIT_USER
from opennem.users.schema import OpenNEMRoles, OpenNEMUser, OpenNEMUserRateLimit

logger = logging.getLogger("opennem.clients.unkey")


# @ttl_cache(maxsize=100, ttl=60 * 5)
async def unkey_validate(api_key: str) -> None | OpenNEMUser:
    """Validate a key with unkey"""

    if not settings.unkey_root_key:
        raise Exception("No unkey root key set")

    if not settings.unkey_api_id:
        raise Exception("No unkey app id set")

    client = unkey.Client(api_key=settings.unkey_root_key)
    await client.start()

    try:
        async with unkey.client.Client() as c:
            result = await c.keys.verify_key(key=api_key, api_id=settings.unkey_api_id)  # type: ignore

        if not result.is_ok:
            logger.warning("Unkey verification failed")
            return None

        if result.is_err:
            err = result.unwrap_err()
            code = (err.code or unkey.models.ErrorCode.Unknown).value
            logger.info(f"Unkey verification failed: {code}")
            return None

        data = result.unwrap()
        logger.debug(f"Unkey response data: {data}")

        # Check if the code is NOT_FOUND and return None if so
        if data.code == ErrorCode.NotFound:
            logger.info("API key not found")
            return None

        if not data.valid:
            logger.info("API key is not valid")
            return None

        if data.error:
            logger.info(f"API key error: {data.error}")
            return None

        if not data.id:
            logger.info("API key id is not valid no id")
            return None

        try:
            model = OpenNEMUser(id=data.id, valid=data.valid, owner_id=data.owner_id, meta=data.meta, error=data.error)

            if data.ratelimit:
                model.rate_limit = OpenNEMUserRateLimit(
                    limit=data.ratelimit.limit, remaining=data.ratelimit.remaining, reset=data.ratelimit.reset
                )

            if data.meta:
                if "roles" in data.meta:
                    for role in data.meta["roles"]:
                        model.roles.append(OpenNEMRoles(role))

            return model
        except ValidationError as ve:
            logger.error(f"Pydantic validation error: {ve}")
            for error in ve.errors():
                logger.error(f"Field: {error['loc'][0]}, Error: {error['msg']}")
            return None

    except Exception as e:
        logger.exception(f"Unexpected error in unkey_validate: {e}")
        return None

    finally:
        await client.close()


async def unkey_create_key(
    email: str, name: str, roles: list[OpenNEMRoles], ratelimit: unkey.Ratelimit | None = None
) -> ApiKey | None:
    """Create a key with unkey"""
    if not settings.unkey_root_key:
        raise Exception("No unkey root key set")

    if not settings.unkey_api_id:
        raise Exception("No unkey app id set")

    prefix = "on"

    if settings.is_dev:
        prefix = "on_dev"

    meta = {"roles": [role.value for role in roles], "email": email, "name": name}

    if not ratelimit:
        ratelimit = OPENNEM_RATELIMIT_USER

        if "pro" in roles:
            ratelimit = OPENNEM_RATELIMIT_PRO

        if "admin" in roles:
            ratelimit = OPENNEM_RATELIMIT_ADMIN

    try:
        async with unkey.client.Client(api_key=settings.unkey_root_key) as c:
            result = await c.keys.create_key(
                api_id=settings.unkey_api_id, name=name, prefix=prefix, meta=meta, owner_id=email, ratelimit=ratelimit
            )

            if not result.is_ok:
                error = result.unwrap_err()
                logger.error(f"Unkey key creation failed: {error}")
                return None

    except Exception as e:
        logger.exception(f"Unexpected error in unkey_create_key: {e}")
        return None

    data = result.unwrap()

    logger.info(f"Unkey key created: {data.key} {data.key_id}")

    return data


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
