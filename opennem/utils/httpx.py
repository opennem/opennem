""" " httpx async client for async http requests"""

import asyncio
import logging
from typing import Any

import chardet
import httpx
import logfire

# from curl_cffi.requests import AsyncSession  # noqa: F401
from httpx import AsyncClient, AsyncHTTPTransport, Request, Response
from httpx._transports.default import AsyncHTTPTransport as DefaultAsyncTransport

from opennem import settings
from opennem.utils.random_agent import get_random_agent
from opennem.utils.version import get_version

logfire.instrument_httpx()

logger = logging.getLogger("opennem.utils.httpx")


DEFAULT_BROWSER_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    ),
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}

API_CLIENT_HEADERS = {"user-agent": f"OpenNEM (v {get_version()})", "accept": "*/*"}


def autodetect_encoding(content) -> str | None:
    return chardet.detect(content).get("encoding")


# debug loggers and interceptors
def debug_log_request(request) -> None:
    logger.debug(f"{request.method} {request.url}")


def debug_log_response(response) -> None:
    request = response.request
    logger.debug(f"Response event hook: {request.method} {request.url} - Status {response.status_code}")


class OpenNEMHTTPTransport(AsyncHTTPTransport):
    """Custom transport that implements retry logic for 403 responses"""

    def __init__(
        self, *args: Any, retries: int = 3, retry_delay: float = 1.0, retry_codes: list[int] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)

        if not retry_codes:
            retry_codes = [403]

        self._retries = retries
        self._retry_delay = retry_delay
        self._retry_codes = retry_codes
        self._transport = DefaultAsyncTransport(*args, **kwargs)

    async def handle_async_request(self, request: Request) -> Response:
        attempts = 0
        last_exception = None

        while attempts <= self._retries:
            try:
                response = await self._transport.handle_async_request(request)

                if response.status_code not in self._retry_codes:
                    return response

                if attempts == self._retries:
                    return response

                attempts += 1
                retry_delay = self._retry_delay * (2 ** (attempts - 1))  # exponential backoff
                logger.warning(
                    f"Received {response.status_code} for {request.url}. "
                    f"Attempt {attempts}/{self._retries}. Retrying in {retry_delay}s"
                )
                await asyncio.sleep(retry_delay)

            except Exception as e:
                last_exception = e
                if attempts == self._retries:
                    raise
                attempts += 1
                retry_delay = self._retry_delay * (2 ** (attempts - 1))
                logger.warning(
                    f"Request failed for {request.url} "
                    f"Status {response.status_code} "
                    f"Attempt {attempts}/{self._retries}. Retrying in {retry_delay}s"
                )
                await asyncio.sleep(retry_delay)

        if last_exception:
            raise last_exception

        return response  # type: ignore


def httpx_factory(
    mimic_browser: bool = False, debug: bool = True, proxy: bool = False, retry_403: bool = True, *args: Any, **kwargs: Any
) -> AsyncClient:
    """Create a new httpx client with default settings

    Args:
        mimic_browser: Whether to mimic a browser with headers
        debug: Enable debug logging
        proxy: Whether to use proxy settings
        retry_403: Whether to enable 403 retries

    Returns:
        AsyncClient: Configured httpx client
    """

    # set default request headers
    headers = kwargs.get("headers", {})

    if mimic_browser:
        headers.setdefault("user-agent", get_random_agent())
        headers.update(DEFAULT_BROWSER_HEADERS)
    else:
        headers.setdefault("user-agent", f"OpenNEM/{get_version()}")

    kwargs["headers"] = headers

    # set default timeout
    if not kwargs.get("timeout"):
        kwargs["timeout"] = settings.http_timeout

    # set default verify
    if not kwargs.get("verify"):
        kwargs["verify"] = settings.http_verify_ssl

    if not kwargs.get("proxy") and proxy and settings.http_proxy_url:
        logger.debug(f"Setting proxy: {settings.http_proxy_url}")
        proxy_mounts = {
            "http://": httpx.AsyncHTTPTransport(proxy=settings.http_proxy_url),
            "https://": httpx.AsyncHTTPTransport(proxy=settings.http_proxy_url),
        }
        kwargs["mounts"] = proxy_mounts

    # set event hooks
    event_hooks = kwargs.get("event_hooks", None)
    if debug:
        event_hooks = event_hooks or {}

        if "request" in event_hooks:
            event_hooks["request"].append(debug_log_request)
        else:
            event_hooks["request"] = [debug_log_request]

    transport_kwargs = {
        "retries": settings.http_retries,
    }

    if retry_403:
        transport_kwargs.update(
            {
                "retry_codes": [403],
                "retry_delay": 1.0,
            }
        )

    return httpx.AsyncClient(
        *args,
        **kwargs,
        transport=OpenNEMHTTPTransport(**transport_kwargs),
        default_encoding=autodetect_encoding,  # type: ignore
    )


http = httpx_factory(debug=settings.is_dev, timeout=settings.http_timeout)

if __name__ == "__main__":
    asyncio.run(http.get("https://httpbin.org/status/403"))
