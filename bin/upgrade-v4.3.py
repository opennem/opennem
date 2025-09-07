#!/usr/bin/env uv run

# sript to upgrade opennem to v4.1

import asyncio

from opennem.crawl import run_crawl
from opennem.crawlers.nemweb import AEMONemwebDispatchIS, AEMONemwebDispatchISArchive


async def upgrade_v4_1():
    # 1. run alembic migrations with ('uv run alembic upgrade head') system command
    await asyncio.create_subprocess_shell("uv run alembic upgrade head")

    # 2. run dispatch both current and historic crawls
    await run_crawl(AEMONemwebDispatchIS, latest=False)
    await run_crawl(AEMONemwebDispatchISArchive, latest=False)

    # 3. refresh clickhouse market aggregate


if __name__ == "__main__":
    asyncio.run(upgrade_v4_1())
