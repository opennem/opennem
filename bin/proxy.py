#!/usr/bin/env python
from opennem.utils.httpx import httpx_factory


async def run_req() -> None:
    """ """
    url = "http://lumtest.com/myip.json"

    async with httpx_factory(mimic_browser=True, proxy=True) as http:
        resp = await http.get(url)
        print(resp.status_code)
        print(resp.request.headers)
        print(resp.json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_req())
