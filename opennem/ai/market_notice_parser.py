# ruff: noqa: E501
"""
Parse AEMO market notices using OpenAI GPT4o-mini

"""

import json
import logging
from datetime import datetime

import instructor

from opennem.ai.openai import get_openai_client
from opennem.schema.market_notice import AEMOMarketNoticeResponseSchema

logger = logging.getLogger("opennem.ai.market_notice_parser")

_SYSTEM_PROMPT = """You are a smart interpreter of text data from AEMO which is the energy regulator in Australia.

They issue notices to the market in the following format:

```
-------------------------------------------------------------------
                           MARKET NOTICE
-------------------------------------------------------------------

From :              AEMO
To   :              NEMITWEB1
Creation Date :     08/07/2024     20:01:41

-------------------------------------------------------------------

Notice ID               :         117325
Notice Type ID          :         INTER-REGIONAL TRANSFER
Notice Type Description :         Inter-Regional Transfer limit variation
Issue Date              :         08/07/2024
External Reference      :         Inter-regional transfer limit variation - Eraring - Newcastle 90 330kV Line - NSW region - 08/07/2024

-------------------------------------------------------------------

Reason :

AEMO ELECTRICITY MARKET NOTICE

Inter-regional transfer limit variation -  Eraring - Newcastle 90 330kV Line  - NSW region - 08/07/2024

At   1940 hrs 08/07/2024 there was an unplanned outage of  Eraring - Newcastle 90 330kV Line

The following constraint set(s) invoked at 1950 hrs 08/07/2024
N-ERNC_90

This constraint set(s) contains equations with the following interconnectors on the LHS.
N-Q-MNSP1,NSW1-QLD1

Refer to the AEMO Network Outage Scheduler for further information.

Manager NEM Real Time Operations

-------------------------------------------------------------------
END OF REPORT
-------------------------------------------------------------------
```

## Input Format

You will be provided a JSON list of input notices


Your task is to extract data from such a notice and parse it back in the JSON schema provided.

"""

_client = instructor.from_openai(get_openai_client())


async def parse_market_notice(market_notices: list[str], time_since: datetime | None = None) -> AEMOMarketNoticeResponseSchema:
    """Parse a market notice using OpenAI GPT4o-mini"""
    completion = await _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(market_notices)},
        ],
        response_model=AEMOMarketNoticeResponseSchema,
        temperature=0,
        max_tokens=16383,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    if time_since:
        # loop through the returns and remove those we don't need
        for notice in completion.notices:
            if notice.creation_date <= time_since:
                logger.debug(f"Removing notice {notice.id} because it is too old")
                completion.notices.remove(notice)

    return completion
