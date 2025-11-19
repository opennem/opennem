import asyncio
import logging
import random
from typing import Any
from urllib.parse import urlparse

import rnet

from opennem import settings

logger = logging.getLogger("opennem.utils.http")


def _get_rnet_proxy() -> rnet.Proxy:
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


def _get_random_rnet_browser() -> rnet.Emulation:
    """get a random emulated browser - pad out the list based on ~popularity"""
    rnet_browsers = [
        rnet.Emulation.Chrome138,
        rnet.Emulation.Chrome138,
        rnet.Emulation.Chrome139,
        rnet.Emulation.Chrome139,
        rnet.Emulation.Chrome139,
        rnet.Emulation.Chrome140,
        rnet.Emulation.Chrome140,
        rnet.Emulation.Chrome140,
        rnet.Emulation.Chrome140,
        rnet.Emulation.Chrome140,
        rnet.Emulation.Edge134,
        rnet.Emulation.Firefox142,
        rnet.Emulation.Firefox143,
        rnet.Emulation.Firefox143,
        rnet.Emulation.Firefox143,
        rnet.Emulation.Safari26,
        rnet.Emulation.Safari26,
        rnet.Emulation.Safari26,
        rnet.Emulation.SafariIos26,
        rnet.Emulation.SafariIos26,
        rnet.Emulation.SafariIos26,
        rnet.Emulation.SafariIPad26,
        rnet.Emulation.Opera119,
    ]
    return random.choice(rnet_browsers)


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
    def is_success(self) -> bool:
        return self.status_code >= 200 and self.status_code < 300

    @property
    def is_error(self) -> bool:
        return self.status_code >= 400 and self.status_code < 500

    @property
    def is_client_error(self) -> bool:
        return self.status_code >= 400 and self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        return self.status_code >= 500 and self.status_code < 600

    @property
    def text(self) -> str:
        return self._text

    @property
    def content(self) -> bytes:
        return self._content

    @property
    def user_agent(self) -> str:
        return self._resp.user_agent

    @property
    def headers(self) -> Any:
        """convert rnet headers to dict"""
        headers: dict[str, str] = {}
        for _header, _value in self._resp.headers:
            headers[_header.decode("utf-8").lower()] = _value.decode("utf-8")
        return headers

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
        emulation = _get_random_rnet_browser() if mimic_browser else None
        self._client = rnet.Client(emulation=emulation)

        self._proxy = None
        if proxy:
            try:
                self._proxy = _get_rnet_proxy()
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

    async def test_retry():
        http = http_factory(proxy=False, debug=True)
        resp = await http.get("https://httpbin.org/status/403")
        print(f"Response status: {resp.status_code}")
        print(f"Response body length: {len(resp.content)}")

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

    async def test_aemo_downloads():
        urls = [
            "https://data.wa.aemo.com.au/public/market-data/wemde/tradingReport/tradingDayReport/previous/TradingDayReport_20231004.zip",
            "https://nemweb.com.au/Reports/Current/DispatchIS_Reports/PUBLIC_DISPATCHIS_202511191035_0000000490006114.zip",
        ]

        http = http_factory(proxy=False, debug=True)

        for url in urls:
            resp = await http.get(url)
            print(f"Response status: {resp.status_code}")
            print(f"Response body length: {len(resp.content)}")

    async def test_fingerprint():
        http = http_factory(proxy=False, debug=True)
        resp = await http.post("https://tls.peet.ws/api/all")
        print(f"Response status: {resp.status_code}")
        print(f"Response body length: {len(resp.content)}")
        print(resp.headers)
        print(resp.content)

    async def test_aemo_downloads_many():
        url = "https://nemweb.com.au/Reports/Current/DispatchIS_Reports/PUBLIC_DISPATCHIS_202511191035_0000000490006114.zip"

        http = http_factory(proxy=True, debug=True)

        semaphore = asyncio.Semaphore(10)
        async with semaphore:
            for _ in range(100):
                resp = await http.get(url)
                print(f"Response status: {resp.status_code} with body length {len(resp.content)}")

    asyncio.run(test_retry())
