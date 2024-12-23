""" " httpx async client for async http requests"""

import logging

import chardet
import httpx
import logfire
from httpx import AsyncClient, AsyncHTTPTransport

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


def autodetect_encoding(content) -> str | None:
    return chardet.detect(content).get("encoding")


# debug loggers and interceptors
def debug_log_request(request) -> None:
    logger.debug(f"{request.method} {request.url}")


def debug_log_response(response) -> None:
    request = response.request
    logger.debug(f"Response event hook: {request.method} {request.url} - Status {response.status_code}")


class OpenNEMHTTPTransport(AsyncHTTPTransport):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def httpx_factory(mimic_browser: bool = False, debug: bool = True, proxy: bool = False, *args, **kwargs) -> AsyncClient:
    """Create a new httpx client with default settings"""

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

    return httpx.AsyncClient(
        *args,
        **kwargs,
        transport=OpenNEMHTTPTransport(retries=settings.http_retries),
        default_encoding=autodetect_encoding,  # type: ignore
    )


http = httpx_factory(debug=settings.is_dev, timeout=settings.http_timeout)


async def get_http(*args, **kwargs) -> AsyncClient:
    """Used in api"""
    http = httpx_factory(*args, **kwargs)
    try:
        yield http
    finally:
        http.aclose()
