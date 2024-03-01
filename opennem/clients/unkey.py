"""unkney client for validating api keys"""

import asyncio

import unkey
from cachetools.func import ttl_cache
from pydantic import BaseModel

from opennem import settings


class UnkneyUser(BaseModel):
    valid: bool
    owner_id: str
    meta: dict | None = None
    error: str | None = None


@ttl_cache(maxsize=100, ttl=60 * 5)
async def unkey_validate(api_key: str) -> None | UnkneyUser:
    """Validate a key with unkey"""

    if not settings.unkey_root_key:
        raise Exception("No unkey root key set")

    client = unkey.Client(api_key=settings.unkey_root_key)
    await client.start()

    result = await client.keys.verify_key(key=api_key)

    if not result.is_ok:
        return None

    data = result.unwrap()

    model = None

    try:
        model = UnkneyUser(**{"valid": data.valid, "owner_id": data.owner_id, "meta": data.meta, "error": data.error})

    except Exception as e:
        raise Exception("Invalid unkey response") from e

    await client.close()

    return model


# debug entry point
if __name__ == "__main__":
    test_key = "ondev_123123123"
    model = asyncio.run(unkey_validate(api_key=test_key))

    print(model)
