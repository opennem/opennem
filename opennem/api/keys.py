import logging

import unkey
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from opennem import settings

logger = logging.getLogger("opennem.api")


# API Keys
unkey_client = unkey.Client(api_key=settings.unkey_root_key)

api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(api_key: str = Depends(api_key_header)):
    result = await unkey_client.keys.verify_key(api_key, settings.unkey_app_id)
    if not result.is_ok or not result.unwrap().valid:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return result.unwrap()
