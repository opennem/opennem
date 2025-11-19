import asyncio
import logging
from typing import Any
from urllib.parse import urlparse

import rnet

from opennem import settings
from opennem.utils.random_agent import get_random_agent
from opennem.utils.version import get_version

logger = logging.getLogger("opennem.utils.http")

DEFAULT_BROWSER_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    ),
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


def get_rnet_proxy() -> rnet.Proxy:
    if not settings.http_proxy_url:
        raise ValueError("Proxy is enabled but no proxy URL is set")

    logger.debug(f"Using proxy: {settings.http_proxy_url}")

    parsed = urlparse(settings.http_proxy_url)

    # Force http scheme for proxy URL as most proxies use HTTP CONNECT
    # even if they are "HTTPS proxies" (meaning they support HTTPS tunneling)
    proxy_scheme = "http" if parsed.scheme == "https" else parsed.scheme

    proxy_url = f"{proxy_scheme}://{parsed.hostname}"

    if parsed.port:
        proxy_url += f":{parsed.port}"

    return rnet.Proxy.all(
        url=proxy_url,
        username=parsed.username,
        password=parsed.password,
    )


class HttpResponse:
    """Wrapper for rnet response to be compatible with httpx.Response"""

    def __init__(self, rnet_resp: Any, content: bytes, text: str) -> None:
        self._resp = rnet_resp
        self._content = content
        self._text = text

    @property
    def status_code(self) -> int:
        # rnet status is a StatusCode object, convert to int
        # Assuming it has standard int conversion or we need to parse
        try:
            return int(str(self._resp.status).split(" ")[0])
        except (ValueError, IndexError):
            # Fallback if format is weird
            return 200

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def headers(self) -> Any:
        return self._resp.headers

    @property
    def url(self) -> str:
        return self._resp.url

    def json(self) -> Any:
        import json

        return json.loads(self._text)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP Error {self.status_code}: {self.text}")


class HttpClient:
    """Wrapper for rnet Client with custom:

    * retry logic
    * retry on 403 for nemweb
    * proxy support
    * mimic browser with rnet
    * sync and async interfaces
    """

    def __init__(
        self,
        mimic_browser: bool = False,
        debug: bool = True,
        proxy: bool = False,
        retry_403: bool = True,
        verify: bool = True,
        timeout: float | None = None,
        headers: dict[str, str] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.debug = debug
        self.retry_403 = retry_403
        self.timeout = timeout
        self.verify = verify
        self.headers = headers or {}

        # rnet specific setup
        emulation = rnet.Emulation.Chrome140 if mimic_browser else None
        self._client = rnet.Client(emulation=emulation)

        self._proxy = None
        if proxy:
            try:
                self._proxy = get_rnet_proxy()
            except ValueError:
                logger.error("Proxy is enabled but no proxy URL is set")

        # Retry settings
        self._retries = settings.http_retries
        self._retry_codes = [408, 429, 500, 502, 503, 504]
        # @note this is custom for nemweb which does a 403
        if retry_403:
            self._retry_codes.append(403)
        self._retry_delay = 1.0

    async def __aenter__(self) -> HttpClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        pass

    async def request(self, method: str, url: str, **kwargs: Any) -> HttpResponse:
        # Merge headers
        req_headers = self.headers.copy()
        if "headers" in kwargs:
            req_headers.update(kwargs.pop("headers"))

        # Handle proxy override
        proxy = kwargs.pop("proxy", self._proxy)

        attempts = 0
        last_exception = None

        while attempts <= self._retries:
            try:
                if self.debug:
                    logger.debug(f"{method.upper()} {url}")

                # Map method string to rnet client method
                rnet_method = getattr(self._client, method.lower())

                # rnet methods signature: url, **kwargs
                # We pass proxy here
                resp = await rnet_method(url, proxy=proxy, headers=req_headers, **kwargs)

                # Pre-load content for compatibility
                content = await resp.bytes()
                text = await resp.text()

                compat_resp = HttpResponse(resp, content, text)

                if compat_resp.status_code in self._retry_codes:
                    if attempts == self._retries:
                        return compat_resp

                    attempts += 1
                    retry_delay = self._retry_delay * (2 ** (attempts - 1))
                    logger.warning(
                        f"Received {compat_resp.status_code} for {url}. "
                        f"Attempt {attempts}/{self._retries}. Retrying in {retry_delay}s"
                    )
                    await asyncio.sleep(retry_delay)
                    continue

                return compat_resp

            except Exception as e:
                last_exception = e
                if attempts == self._retries:
                    raise

                attempts += 1
                retry_delay = self._retry_delay * (2 ** (attempts - 1))
                logger.warning(f"Request failed for {url} Attempt {attempts}/{self._retries}. Retrying in {retry_delay}s")
                await asyncio.sleep(retry_delay)

        if last_exception:
            raise last_exception

        # Should not reach here
        raise Exception("Unknown error in request loop")

    async def get(self, url: str, **kwargs: Any) -> HttpResponse:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> HttpResponse:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> HttpResponse:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> HttpResponse:
        return await self.request("DELETE", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> HttpResponse:
        return await self.request("PATCH", url, **kwargs)

    async def head(self, url: str, **kwargs: Any) -> HttpResponse:
        return await self.request("HEAD", url, **kwargs)

    async def options(self, url: str, **kwargs: Any) -> HttpResponse:
        return await self.request("OPTIONS", url, **kwargs)


def http_factory(
    mimic_browser: bool = True,
    debug: bool = False,
    proxy: bool = False,
    retry_403: bool = True,
    *args: Any,
    **kwargs: Any,
) -> HttpClient:
    """
    Create a new http client with default settings
    Interface compatible with httpx_factory

    Params:

    * mimic_browser: Whether to mimic a browser with headers
    * debug: Enable debug logging
    * proxy: Whether to use proxy settings
    * retry_403: Whether to enable 403 retries
    * args: Additional arguments to pass to the client
    * kwargs: Additional keyword arguments to pass to the client

    Returns:
    * HttpClient: Configured http client

    Example:
    ```python
    client = http_factory(mimic_browser=True, debug=True, proxy=True, retry_403=True)
    resp = await client.get("https://httpbin.org/status/403")
    print(resp.status_code)
    print(resp.text)
    ```
    """

    # Defaults logic
    headers = kwargs.get("headers", {})

    if mimic_browser:
        headers.setdefault("user-agent", get_random_agent())
        headers.update(DEFAULT_BROWSER_HEADERS)
    else:
        headers.setdefault("user-agent", f"OpenNEM/{get_version()}")

    kwargs["headers"] = headers

    # Default timeout
    if not kwargs.get("timeout"):
        kwargs["timeout"] = settings.http_timeout

    # Default verify
    if not kwargs.get("verify"):
        kwargs["verify"] = settings.http_verify_ssl

    return HttpClient(mimic_browser=mimic_browser, debug=debug, proxy=proxy, retry_403=retry_403, **kwargs)


# Global client instance
http = http_factory(debug=settings.is_dev)


if __name__ == "__main__":

    async def test_client():
        print(f"Testing client with proxy setting: {settings.http_proxy_url}")

        # Test with proxy enabled
        client = http_factory(proxy=True, debug=True)

        try:
            # Test 403 retry or just IP check
            resp = await client.get("https://lumtest.com/myip.json")
            print(f"Response status: {resp.status_code}")
            print(f"Response body: {resp.text}")
        except Exception as e:
            print(f"Request failed: {e}")

    asyncio.run(test_client())
