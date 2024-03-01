#!/usr/bin/env python
"""AEMO 5MIN Data Parser from vizualizations page"""

import logging
from datetime import datetime
from enum import Enum
from json.decoder import JSONDecodeError
from typing import Any

import requests
from pydantic import ConfigDict
from pydantic.main import BaseModel

from opennem.core.normalizers import blockwords_to_snake_case
from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger("opennem.parser.aemo.viz")

AEMO_5MIN_API_ENDPOINT = "https://visualisations.aemo.com.au/aemo/apps/api/report/5MIN"
AEMO_5MIN_RESPONSE_KEY = "5MIN"


class AEMOPeriodType(Enum):
    actual = "ACTUAL"
    scheduled = "SCHEDULED"
    forecast = "FORECAST"


class AEMO5MinAPIResponse(BaseModel):
    settlement_date: datetime
    period_type: AEMOPeriodType
    net_interchange: float | None
    region_id: str
    rrp: float
    scheduled_generation: float
    semi_scheduled_generation: float
    total_demand: float

    @property
    def is_forecast(self) -> bool:
        return self.period_type == AEMOPeriodType.scheduled

    model_config = ConfigDict(alias_generator=blockwords_to_snake_case, from_attributes=True, str_strip_whitespace=True)


def get_aemo_viz_request_headers() -> dict[str, str]:
    """http request headers for AEMO viz"""
    return {
        "User-Agent": get_random_agent(),
        "Origin": "https://visualisations.aemo.com.au",
        "Referer": "https://visualisations.aemo.com.au/aemo/apps/visualisation/index.html",
    }


def obj_blockwords_to_snake(obj: dict[str, Any]) -> dict[str, Any]:
    """Converts block cased keys in a dict like SETTLEMENTDATE into settlement_date"""
    return {blockwords_to_snake_case(k): v for k, v in obj.items()}


def get_aemo_5min_data(interval: str = "5MIN") -> dict | None:
    interval = interval.upper()

    if interval not in ["5MIN", "30MIN"]:
        raise Exception(f"Not a supported interval: {interval}")

    r = requests.post(
        AEMO_5MIN_API_ENDPOINT,
        json={"timescale": [interval]},
        headers=get_aemo_viz_request_headers(),
    )

    if not r.ok:
        logger.error(f"Response {r.status_code}: {str(r.content)}")
        logger.debug(r.request.headers)
        logger.debug(r.headers)
        return None

    try:
        resp_json = r.json()
    except JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        logger.debug(r.content)
        return None

    if not isinstance(resp_json, dict):
        logger.error("Did not get correct response type")
        return None

    if AEMO_5MIN_RESPONSE_KEY not in resp_json:
        logger.error(f"Response key {AEMO_5MIN_RESPONSE_KEY} missing in payload.")
        return None

    return resp_json


def aemo_parse_5min_api(aemo_response_data: dict) -> list[AEMO5MinAPIResponse]:
    """Parse the viz response into models"""
    model_response = [AEMO5MinAPIResponse(**obj_blockwords_to_snake(i)) for i in aemo_response_data[AEMO_5MIN_RESPONSE_KEY]]

    return model_response


def get_aemo_5min(interval_size: str = "5MIN") -> list[AEMO5MinAPIResponse]:
    """Run the live get and parse it"""
    aemo_viz_data = get_aemo_5min_data(interval=interval_size)

    if not aemo_viz_data:
        logger.error("No response data")
        return []

    response_models = aemo_parse_5min_api(aemo_viz_data)

    return response_models


# debug entry point
if __name__ == "__main__":
    records = get_aemo_5min()

    from pprint import pprint

    pprint(records)
