import logging
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError

from opennem.core.normalizers import (
    clean_float,
    normalize_aemo_region,
    normalize_duid,
)
from opennem.utils.dates import parse_date

logger = logging.getLogger(__name__)


def mms_alias_generator(name: str) -> str:
    """
    This method aliases those capitalised aemo
    names into something more sensible for python
    access
    """
    _name = name.upper()

    return _name


def validate_date(date_value: str) -> datetime:
    dt = parse_date(date_value)

    if not dt:
        raise ValueError("Not a valid date: {}".format(date_value))

    return dt


def capitalize_string(string_val: str) -> str:
    return string_val.capitalize()


class MMSBase(BaseModel):
    class Config:
        anystr_strip_whitespace = True
        use_enum_values = True
        arbitrary_types_allowed = True
        validate_assignment = True
        allow_population_by_field_name = True
        alias_generator = mms_alias_generator


# pylint: disable=no-self-argument
class ParticipantMNSPInterconnector(MMSBase):
    """"""

    linkid: str
    effectivedate: datetime
    interconnectorid: str
    fromregion: str
    toregion: str
    maxcapacity: float
    authoriseddate: datetime

    @validator("linkid", pre=True)
    def validate_linkid(cls, value: str) -> str:
        return normalize_duid(value)

    @validator("effectivedate", pre=True)
    def validate_effectivedate(cls, value: str) -> datetime:
        dt = parse_date(value)

        if not dt:
            raise ValueError("Not a valid date: {}".format(value))

        return dt

    @validator("maxcapacity", pre=True)
    def validate_maxcapacity(cls, value: str) -> float:
        f = clean_float(value)

        if not f:
            raise ValueError("Not a valid capacity: {}".format(value))

        return f

    @validator("authoriseddate", pre=True)
    def validate_authoriseddate(cls, value: str) -> datetime:
        dt = parse_date(value)

        if not dt:
            logger.error("Not a valid date: {}".format(value))
            raise ValueError("Not a valid authoriseddate: {}".format(value))

        return dt


# pylint: disable=no-self-argument
class MarketConfigInterconnector(MMSBase):
    """"""

    interconnectorid: str
    regionfrom: str
    regionto: str
    description: str
    lastchanged: datetime

    # validators
    _validate_description = validator("description")(capitalize_string)
    _validate_lastchanged = validator("lastchanged", pre=True)(validate_date)


# Map AEMO full table names to schemas
TABLE_TO_SCHEMA_MAP = {
    "PARTICIPANT_REGISTRATION_MNSP_INTERCONNECTOR": ParticipantMNSPInterconnector,
    "MARKET_CONFIG_INTERCONNECTOR": MarketConfigInterconnector,
}


def get_mms_schema_for_table(table_name: str) -> Optional[MMSBase]:
    if table_name not in TABLE_TO_SCHEMA_MAP.keys():
        logger.info("No schema found for table: {}".format(table_name))
        return None

    return TABLE_TO_SCHEMA_MAP[table_name]
