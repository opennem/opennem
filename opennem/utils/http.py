import logging

import rnet

from opennem import settings

logger = logging.getLogger("opennem.utils.http")

_DEFAULT_BROWSER_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    ),
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",  # noqa: E501
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}


def get_rnet_client(mimic_browser: bool = True) -> rnet.Client:
    """Get a rnet client"""

    emulation = rnet.Emulation.Chrome140 if mimic_browser else None

    client = rnet.Client(emulation=emulation)  # type: ignore

    return client


def get_rnet_proxy() -> rnet.Proxy:
    if not settings.http_proxy_url:
        raise ValueError("Proxy is enabled but no proxy URL is set")

    logger.debug(f"Using proxy: {settings.http_proxy_url}")

    return rnet.Proxy.all(
        url=settings.http_proxy_url,
        custom_http_headers=_DEFAULT_BROWSER_HEADERS,
    )


async def proxy_test():
    resp = await get_rnet_client().get(url="https://lumtest.com/myip.json", proxy=get_rnet_proxy())

    print(await resp.json())


if __name__ == "__main__":
    import asyncio

    async def test_client():
        client = get_rnet_client()

        resp = await client.get("https://httpbin.org/status/403")
        print(resp.headers)

    asyncio.run(proxy_test())
