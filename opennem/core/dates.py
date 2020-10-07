import logging
from datetime import datetime
from typing import Optional, Union

from dateutil import parser

from opennem.core.networks import NetworkSchema

logger = logging.getLogger(__name__)


def parse_date(
    date_str: Union[str, datetime], network: Optional[NetworkSchema] = None
) -> datetime:
    dt_return = None

    if type(date_str) is datetime:
        dt_return = date_str

    try:
        if type(date_str) is str:
            dt_return = parser.parse(date_str)
    except Exception as e:
        logger.error(e)

    if network:
        tz = network.get_timezone()
        dt_return = tz.localize(dt_return)

    return dt_return
