"""A failed proxy falls back to a direct connection, then cools down before it is tried again."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from opennem.utils import http

PROXY = object()


def _response(status: int = 200, body: bytes = b"ok") -> SimpleNamespace:
    return SimpleNamespace(
        status=f"{status} OK",
        bytes=AsyncMock(return_value=body),
        text=AsyncMock(return_value=body.decode()),
        headers=[],
        url="https://www.nemweb.com.au/",
    )


@pytest.fixture(autouse=True)
def _proxy_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(http, "_proxy_down_until", 0.0)
    monkeypatch.setattr(http, "_get_rnet_proxy", lambda: PROXY)


def _client(get: AsyncMock) -> http.HttpClient:
    client = http.http_factory(proxy=True, mimic_browser=False)
    client._client = SimpleNamespace(get=get)  # type: ignore[assignment]
    return client


def _proxied(get: AsyncMock) -> list[bool]:
    return [c.kwargs["proxy"] is PROXY for c in get.await_args_list]


def test_proxy_error_goes_direct_without_sleeping() -> None:
    async def _get(url: str, proxy: object = None, **kwargs: object) -> SimpleNamespace:
        if proxy is not None:
            raise TimeoutError("proxy hung")
        return _response(body=b"direct")

    get = AsyncMock(side_effect=_get)
    with patch.object(http.asyncio, "sleep", AsyncMock()) as sleep:
        resp = asyncio.run(_client(get).get("https://www.nemweb.com.au/x.zip"))

    assert resp.content == b"direct"
    assert _proxied(get) == [True, False]
    sleep.assert_not_awaited()


def test_proxy_auth_refusal_goes_direct() -> None:
    async def _get(url: str, proxy: object = None, **kwargs: object) -> SimpleNamespace:
        return _response(407, b"proxy auth") if proxy is not None else _response(body=b"direct")

    get = AsyncMock(side_effect=_get)
    resp = asyncio.run(_client(get).get("https://www.nemweb.com.au/x.zip"))

    assert resp.status_code == 200
    assert _proxied(get) == [True, False]


def test_down_proxy_is_skipped_until_the_cooldown_ends(monkeypatch: pytest.MonkeyPatch) -> None:
    now = [1000.0]
    monkeypatch.setattr(http.time, "monotonic", lambda: now[0])

    async def _get(url: str, proxy: object = None, **kwargs: object) -> SimpleNamespace:
        if proxy is not None:
            raise ConnectionError("tunnel failed")
        return _response()

    get = AsyncMock(side_effect=_get)
    client = _client(get)

    asyncio.run(client.get("https://www.nemweb.com.au/a.zip"))
    # a second client in the same process shares the outage
    asyncio.run(_client(get).get("https://www.nemweb.com.au/b.zip"))
    assert _proxied(get) == [True, False, False]

    now[0] += http.PROXY_COOLDOWN_SECONDS
    asyncio.run(client.get("https://www.nemweb.com.au/c.zip"))
    assert _proxied(get) == [True, False, False, True, False]


def test_upstream_error_status_through_the_proxy_keeps_the_proxy() -> None:
    """A 403 from nemweb is the upstream answering, so the usual retries apply via the proxy"""
    get = AsyncMock(side_effect=[_response(403, b"no"), _response(body=b"yes")])
    with patch.object(http.asyncio, "sleep", AsyncMock()):
        resp = asyncio.run(_client(get).get("https://www.nemweb.com.au/x.zip"))

    assert resp.content == b"yes"
    assert _proxied(get) == [True, True]
    assert http._proxy_is_up()


def test_direct_client_errors_still_retry_then_raise() -> None:
    client = http.http_factory(proxy=False, mimic_browser=False)
    get = AsyncMock(side_effect=ConnectionError("down"))
    client._client = SimpleNamespace(get=get)  # type: ignore[assignment]

    with patch.object(http.asyncio, "sleep", AsyncMock()), pytest.raises(ConnectionError):
        asyncio.run(client.get("https://www.nemweb.com.au/x.zip"))

    assert get.await_count == client._retries + 1
    assert http._proxy_is_up()
