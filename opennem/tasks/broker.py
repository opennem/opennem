"""
OpenNEM Broker Module

This module is responsible for managing the connection to the Redis server using the arq library.
It provides a function to get a Redis connection pool which can be used for scheduling tasks and other operations.

For more information on the arq library, see the official documentation:
https://arq-docs.helpmanual.io/

"""

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from opennem import settings

REDIS_SETTINGS = RedisSettings(
    host=settings.redis_url.host,  # type: ignore
    port=settings.redis_url.port,  # type: ignore
    username=settings.redis_url.username,  # type: ignore
    password=settings.redis_url.password,  # type: ignore
    ssl=settings.redis_url.scheme == "rediss",
    conn_timeout=300,
)


async def get_redis_pool() -> ArqRedis:
    return await create_pool(REDIS_SETTINGS)
