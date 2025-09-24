"""
Utilities for facility outputs

"""

import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger("opennem.api.facilities.utils")


class DateSpecificity(Enum):
    """Date specificity enum"""

    YEAR = "year"
    MONTH = "month"
    QUARTER = "quarter"
    DAY = "day"


def serialize_datetime_specificity(dt: datetime | None, specificity: str | None) -> str | None:
    """Takes a datetime and a specificity and returns a serialized string.ArithmeticError


    For ex. "2025-09-15" with a specificity of "year" returns "2025"
    """
    if not dt:
        return None

    # with no specificity, return the full date
    if not specificity:
        return dt.strftime("%Y-%m-%d")

    # if the specificity is invalid, log a warning and return the full date
    if specificity not in DateSpecificity:
        logger.warning(f"Invalid specificity: {specificity}")

    match specificity:
        case "year":
            return dt.strftime("%Y")
        case "month" | "quarter":
            return dt.strftime("%Y-%m")
        case "day":
            return dt.strftime("%Y-%m-%d")
        case _:
            return dt.strftime("%Y-%m-%d")
