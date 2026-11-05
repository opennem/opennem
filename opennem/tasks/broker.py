"""
OpenNEM Broker Module

This module is responsible for managing the connection to the Redis server using the arq library.
It provides a function to get a Redis connection pool which can be used for scheduling tasks and other operations.

For more information on the arq library, see the official documentation:
https://arq-docs.helpmanual.io/

Connection hardening (BACKEND-69S/6B0): the worker polls `ZRANGEBYSCORE arq:queue` every 0.5s; a silently dropped
TCP connection (VPC/managed redis idle reaping) used to hang the read until the kernel gave up with ETIMEDOUT and
crash the worker. arq's RedisSettings (0.27) only exposes retry/retry_on_timeout/retry_on_error, so keepalive,
socket timeout and health checks are applied to the pool's connection kwargs after arq builds it.
"""

import socket
from typing import Any

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from opennem import settings

# a read that takes longer than this is a dead connection, not a slow command (largest is the startup flushdb)
REDIS_SOCKET_TIMEOUT_S = 30.0
# PING before a command on a connection idle longer than this; reconnects if the server dropped it
REDIS_HEALTH_CHECK_INTERVAL_S = 30
REDIS_RETRIES = 3

# linux TCP keepalive: probe after 60s idle, every 10s, drop after 3 misses. Missing constants (macOS) are skipped.
_KEEPALIVE_SPEC = (("TCP_KEEPIDLE", 60), ("TCP_KEEPINTVL", 10), ("TCP_KEEPCNT", 3))


def keepalive_options() -> dict[int, int]:
    return {getattr(socket, name): value for name, value in _KEEPALIVE_SPEC if hasattr(socket, name)}


def connection_options() -> dict[str, Any]:
    """redis-py Connection kwargs arq's RedisSettings (0.27) can't carry."""
    return {
        "socket_keepalive": True,
        "socket_keepalive_options": keepalive_options(),
        "socket_timeout": REDIS_SOCKET_TIMEOUT_S,
        "health_check_interval": REDIS_HEALTH_CHECK_INTERVAL_S,
    }


REDIS_SETTINGS = RedisSettings(
    host=settings.redis_url.host,  # type: ignore
    port=settings.redis_url.port,  # type: ignore
    username=settings.redis_url.username,  # type: ignore
    password=settings.redis_url.password,  # type: ignore
    ssl=settings.redis_url.scheme == "rediss",
    conn_timeout=300,
    # reconnect + retry a single command that timed out / lost its connection (the ZRANGEBYSCORE poll).
    # retry_on_timeout stays False on purpose: redis-py keys pipeline retries off it, and a retried
    # MULTI/EXEC (arq's retry-counter INCR, ZINCRBY defer) could double-apply. Pipelines raise as before.
    retry=Retry(ExponentialBackoff(cap=10, base=1), REDIS_RETRIES),
    retry_on_error=[RedisConnectionError, RedisTimeoutError],
)


async def apply_connection_options(pool: ArqRedis) -> ArqRedis:
    """Set keepalive/timeout/health-check on every connection the pool makes from now on.

    arq's create_pool already opened (and pinged) a connection with the old kwargs; drop it so the next
    command connects with the new ones.
    """
    cp = pool.connection_pool
    cp.connection_kwargs.update(connection_options())
    await cp.disconnect()
    cp.reset()
    return pool


async def get_redis_pool(redis_settings: RedisSettings = REDIS_SETTINGS) -> ArqRedis:
    return await apply_connection_options(await create_pool(redis_settings))
