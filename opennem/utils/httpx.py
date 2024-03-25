""" " httpx async client for async http requests"""

import logging

import chardet
import httpx
from httpx import AsyncClient, AsyncHTTPTransport

from opennem import __version__, settings

logger = logging.getLogger("opennem.utils.httpx")

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/116.0"

DEFAULT_BROWSER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "accept-encoding": "gzip, deflate",
    "scheme": "https",
    "sec-ch-prefers-color-scheme": "light",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}


def autodetect_encoding(content) -> str | None:
    return chardet.detect(content).get("encoding")


# debug loggers and interceptors
def debug_log_request(request) -> None:
    logger.debug(f"{request.method} {request.url}")


def debug_log_response(response) -> None:
    request = response.request
    logger.debug(f"Response event hook: {request.method} {request.url} - Status {response.status_code}")


def httpx_factory(mimic_browser: bool = False, debug: bool = True, *args, **kwargs) -> AsyncClient:
    """Create a new httpx client with default settings"""

    # set default request headers
    headers = kwargs.get("headers", {})

    if mimic_browser:
        headers.setdefault("user-agent", DEFAULT_USER_AGENT)
        headers.update(DEFAULT_BROWSER_HEADERS)
    else:
        headers.setdefault("user-agent", f"OpenNEM/{__version__}")

    kwargs["headers"] = headers

    # set default timeout
    if not kwargs.get("timeout"):
        kwargs["timeout"] = settings.http_timeout

    # set default verify
    if not kwargs.get("verify"):
        kwargs["verify"] = settings.http_verify_ssl

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
        default_encoding=autodetect_encoding,  # type: ignore
    )


http_transport = AsyncHTTPTransport(retries=settings.http_retries)
http = httpx_factory(
    debug=settings.is_dev, timeout=settings.http_timeout, transport=http_transport, proxy=settings.http_proxy_url
)


async def get_http(*args, **kwargs) -> AsyncClient:
    """Used in api"""
    http = httpx_factory(*args, **kwargs)
    try:
        yield http
    finally:
        http.aclose()
