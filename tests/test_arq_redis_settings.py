"""arq redis pool hardening (BACKEND-69S): keepalive, socket timeout, health check, retry on timeout/connection loss."""

import pytest
from arq import ArqRedis
from arq.connections import RedisSettings
from redis.asyncio.connection import SSLConnection
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from opennem.tasks import broker

pytestmark = pytest.mark.asyncio


async def test_redis_settings_fields_supported_by_arq() -> None:
    s = broker.REDIS_SETTINGS
    assert isinstance(s, RedisSettings)
    assert s.retry_on_timeout is False  # pipelines (MULTI/EXEC) must not be retried
    assert s.retry_on_error is not None
    assert RedisConnectionError in s.retry_on_error and RedisTimeoutError in s.retry_on_error
    assert s.retry is not None and s.retry._retries == broker.REDIS_RETRIES
    assert s.conn_timeout == 300


async def test_connection_options() -> None:
    a = broker.connection_options()
    assert a["socket_keepalive"] is True
    assert a["socket_timeout"] == broker.REDIS_SOCKET_TIMEOUT_S
    assert a["health_check_interval"] == broker.REDIS_HEALTH_CHECK_INTERVAL_S


async def _pool(monkeypatch: pytest.MonkeyPatch, rs: RedisSettings) -> ArqRedis:
    async def _ping(self, *a, **k) -> bool:  # no server: arq's create_pool pings once
        return True

    monkeypatch.setattr(ArqRedis, "ping", _ping)
    return await broker.get_redis_pool(rs)


@pytest.mark.parametrize("ssl", [True, False])
async def test_pool_connections_carry_options(monkeypatch: pytest.MonkeyPatch, ssl: bool) -> None:
    """Through arq's real create_pool, incl. the DO managed redis TLS form (rediss, :25061)."""
    rs = RedisSettings(
        host="redis.example.internal",
        port=25061,
        username="default",
        password="x",
        ssl=ssl,
        conn_timeout=300,
        retry=broker.REDIS_SETTINGS.retry,
        retry_on_error=broker.REDIS_SETTINGS.retry_on_error,
    )
    pool = await _pool(monkeypatch, rs)
    conn = pool.connection_pool.make_connection()
    assert isinstance(conn, SSLConnection) is ssl
    assert conn.socket_keepalive is True
    assert conn.socket_keepalive_options == broker.keepalive_options()
    assert conn.socket_timeout == broker.REDIS_SOCKET_TIMEOUT_S
    assert conn.socket_connect_timeout == 300  # arq's conn_timeout still wins for connect
    assert conn.health_check_interval == broker.REDIS_HEALTH_CHECK_INTERVAL_S
    assert RedisConnectionError in conn.retry_on_error
    assert RedisTimeoutError in conn.retry_on_error
    assert conn.retry_on_timeout is False
    assert len(broker.REDIS_SETTINGS.retry_on_error or []) == 2  # shared list not grown per connection
    assert conn.retry._retries == broker.REDIS_RETRIES
    assert conn.port == 25061 and conn.username == "default"
    await pool.close(close_connection_pool=True)


async def test_apply_drops_connection_made_before_options() -> None:
    """arq's create_pool pings on a connection built without the options; it must not be reused."""
    pool = ArqRedis(host="redis.example.internal", port=25061)
    cp = pool.connection_pool
    old = cp.make_connection()
    cp._available_connections.append(old)
    assert not old.socket_keepalive
    await broker.apply_connection_options(pool)
    assert cp._available_connections == []
    new = cp.make_connection()
    assert new is not old and new.socket_keepalive is True
    await pool.close(close_connection_pool=True)


async def test_plain_command_retries_on_timeout_pipeline_does_not(monkeypatch: pytest.MonkeyPatch) -> None:
    """ZRANGEBYSCORE (plain command) reconnects and retries; a MULTI/EXEC pipeline still raises."""
    rs = RedisSettings(
        host="redis.example.internal",
        retry=broker.REDIS_SETTINGS.retry,
        retry_on_error=broker.REDIS_SETTINGS.retry_on_error,
    )
    pool = await _pool(monkeypatch, rs)
    conn = pool.connection_pool.make_connection()
    calls = {"n": 0}

    async def flaky_send(self, *a, **k) -> list[bytes]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RedisTimeoutError("Timeout reading from x")
        return []

    async def noop(self, *a, **k) -> None:
        return None

    monkeypatch.setattr(type(pool), "_send_command_parse_response", flaky_send)

    async def not_readable(self, *a, **k) -> bool:
        return False

    monkeypatch.setattr(type(conn), "disconnect", noop)
    monkeypatch.setattr(type(conn), "connect", noop)
    monkeypatch.setattr(type(conn), "can_read_destructive", not_readable)
    monkeypatch.setattr(conn.retry, "_backoff", type("B", (), {"compute": lambda self, f: 0, "reset": lambda self: None})())
    pool.connection_pool._available_connections.append(conn)
    pool.connection_pool._created_connections = 1
    assert await pool.zrangebyscore("arq:queue", 0, 1) == []
    assert calls["n"] == 2

    execs = {"n": 0}

    async def timeout_exec(self, *a, **k) -> None:
        execs["n"] += 1
        raise RedisTimeoutError("Timeout reading from x")

    from redis.asyncio.client import Pipeline

    monkeypatch.setattr(Pipeline, "_execute_transaction", timeout_exec)
    with pytest.raises(RedisTimeoutError):
        async with pool.pipeline(transaction=True) as tr:
            tr.incr("arq:retry:x")
            await tr.execute()
    assert execs["n"] == 1  # EXEC not re-sent: a retried INCR could double-count job tries
