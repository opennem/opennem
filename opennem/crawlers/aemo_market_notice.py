""" "
Parses market notices at:

https://www.nemweb.com.au/REPORTS/CURRENT/Market_Notice/


"""

import logging
from datetime import datetime
from textwrap import dedent

from sqlalchemy import func, select

from opennem import settings
from opennem.ai.market_notice_parser import parse_market_notice
from opennem.clients.slack import slack_message
from opennem.core.parsers.dirlisting import get_dirlisting
from opennem.db import get_read_session, get_write_session
from opennem.db.models.opennem import AEMOMarketNotice
from opennem.schema.market_notice import AEMOMarketNoticeSchema, AEMOMarketNoticeType
from opennem.utils.httpx import httpx_factory

logger = logging.getLogger("opennem.crawlers.aemo_market_notice")


_MARKET_NOTICE_URL = "https://www.nemweb.com.au/REPORTS/CURRENT/Market_Notice/"


_http = httpx_factory()


async def _get_market_notice_file(url: str) -> str:
    """given a market notice url return the content"""
    req = await _http.get(url)
    content = req.text

    return content


async def _run_aemo_market_notice_craw(
    time_since: datetime | None = None, limit: int | None = None
) -> list[AEMOMarketNoticeSchema]:
    """
    Crawls the market notice endpoint
    """

    dirlisting = await get_dirlisting(_MARKET_NOTICE_URL)

    market_notices = []
    market_notice_models: list[AEMOMarketNoticeSchema] = []
    notices_processed = 0

    for notice_file in dirlisting.get_files(accepted_extensions=[]):
        if time_since and notice_file.modified_date < time_since:
            continue

        content = await _get_market_notice_file(notice_file.link)
        notices_processed += 1

        if limit and notices_processed > limit:
            break

        market_notices.append(content)

        if len(market_notices) >= 5:
            market_notice_response = await parse_market_notice(market_notices=market_notices, time_since=time_since)
            market_notice_models += market_notice_response.notices
            market_notices = []

    # clear remaining notices
    if market_notices:
        market_notice_response = await parse_market_notice(market_notices=market_notices, time_since=time_since)
        market_notice_models += market_notice_response.notices

    logger.info(f"Got {len(market_notice_models)} response models")

    return market_notice_models


async def _persist_market_notices(notices: list[AEMOMarketNoticeSchema]) -> int:
    """Take a list of market notices and persist them to the database"""
    persisted_count = 0

    async with get_write_session() as session:
        for notice in notices:
            # check if notice is already in database
            existing_notice = await session.get(AEMOMarketNotice, notice.id)
            if existing_notice:
                logger.info(f"Notice {notice.id} already exists in the database. Skipping.")
                continue

            db_notice = AEMOMarketNotice(
                notice_id=notice.id,
                notice_type=notice.notice_type.value,
                creation_date=notice.creation_date,
                issue_date=notice.issue_date,
                external_reference=notice.external_reference,
                reason=notice.reason,
            )
            session.add(db_notice)
            persisted_count += 1

        await session.commit()

    return persisted_count


async def _send_market_notice_slack(notice: AEMOMarketNoticeSchema) -> None:
    """send a slack alert for a market notice"""

    formatted_issue_date = notice.issue_date.strftime("%A %-d %b %I:%M:%S %p")

    message = f"""{notice.id} - *{notice.notice_type.value}* @ {formatted_issue_date}

*{notice.external_reference.strip()}*

```
{notice.reason.strip()}
```
"""

    tag_users = []

    if notice.notice_type in [AEMOMarketNoticeType.market_systems]:
        tag_users = ["@nik"]

    await slack_message(webhook_url=settings.slack_hook_aemo_market_notices, message=dedent(message), tag_users=tag_users)


async def _get_last_notice_date() -> datetime | None:
    """Query the database to get the newest market notice date"""
    async with get_read_session() as session:
        result = await session.execute(select(func.max(AEMOMarketNotice.creation_date)))
        max_date = result.scalar()
    return max_date


async def run_market_notice_update() -> None:
    """run the market notice update"""

    latest_notice = await _get_last_notice_date()

    logger.info(f"Latest notice is: {latest_notice}")

    notices = await _run_aemo_market_notice_craw(time_since=latest_notice, limit=10)

    logger.info(f"Got {len(notices)} notices")

    await _persist_market_notices(notices)

    for notice in notices:
        await _send_market_notice_slack(notice)


if __name__ == "__main__":
    import asyncio

    notices = asyncio.run(run_market_notice_update())
