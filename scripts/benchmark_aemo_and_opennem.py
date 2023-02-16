#!/usr/bin/env python3
"""
This is a script that will check how long it takes after each NEM interval for the data
to be available on NEMWEB. It will then compare that to the time it takes for the data
to appear on OpenNEM.

We first test scada data (DISPATCH_SCADA) vs it being available at OpenNEM in the power
series (ie. 7d.json)
"""


import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp

NEMWEB_URL = "http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"
OPENNEM_URL = "http://api.opennem.org.au/v3/series/7d.json"


def get_now() -> datetime:
    """Returns now in current timezone"""
    return datetime.now().astimezone(ZoneInfo("Australia/Sydney"))


async def get_page(session: aiohttp.ClientSession, url: str) -> str:
    """As advertised in the name"""
    async with session.get(url) as response:
        return await response.text()


async def check_for_changes(session: aiohttp.ClientSession, url: str, previous_content: str) -> str:
    while True:
        current_content = await get_page(session, url)
        if current_content != previous_content:
            print("Change detected!")
            return current_content
        await asyncio.sleep(1)


async def main() -> None:
    async with aiohttp.ClientSession() as session:
        url: str = "https://www.example.com"
        initial_content: str = await get_page(session, url)
        while True:
            await asyncio.sleep(300)
            previous_content: str = initial_content
            initial_content = await check_for_changes(session, url, previous_content)


if __name__ == "__main__":
    asyncio.run(main())
