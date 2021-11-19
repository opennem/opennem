# pylint: disable=no-self-argument
import logging
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError

from opennem.core.normalizers import clean_float, normalize_aemo_region, normalize_duid
from opennem.schema.network import NetworkNEM
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
    _interval_field: Optional[str]
    _primary_keys: Optional[List[str]] = None

    class Config:
        anystr_strip_whitespace = True
        use_enum_values = True
        arbitrary_types_allowed = True
        validate_assignment = True
        allow_population_by_field_name = True
        alias_generator = mms_alias_generator

    _validate_interval_datetime = validator(
        "interval_datetime", pre=True, allow_reuse=True, check_fields=False
    )(lambda x: parse_date(x, network=NetworkNEM))

    _validate_settlementdate = validator(
        "settlementdate", pre=True, allow_reuse=True, check_fields=False
    )(lambda x: parse_date(x, network=NetworkNEM))

    _validate_lastchanged = validator(
        "lastchanged", pre=True, allow_reuse=True, check_fields=False
    )(lambda x: parse_date(x, network=NetworkNEM))


class ParticipantMNSPInterconnector(MMSBase):
    """"""

    linkid: str
    effectivedate: datetime
    versionno: int
    interconnectorid: str
    fromregion: str
    toregion: str
    maxcapacity: float
    tlf: Optional[float]
    lhsfactor: Optional[float]
    meterflowconstant: Optional[float]
    authoriseddate: datetime
    authorisedby: str
    lastchanged: Optional[datetime]
    from_region_tlf: Optional[float]
    to_region_tlf: Optional[float]

    @validator("linkid", pre=True)
    def validate_linkid(cls, value: str) -> Optional[str]:
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

    @validator("lastchanged", pre=True)
    def validate_lastchanged(cls, value: Optional[str]) -> Optional[datetime]:
        if not value or value == "":
            return None

        dt = parse_date(value)

        if not dt:
            logger.error("Not a valid date: {}".format(value))
            raise ValueError("Not a valid lastchanged: {}".format(value))

        return dt


class ParticipantRegistrationStadualloc(MMSBase):
    """"""

    pass


class MarketConfigInterconnector(MMSBase):
    """"""

    interconnectorid: str
    regionfrom: str
    regionto: str
    description: str
    lastchanged: datetime

    # validators
    _validate_description = validator("description")(capitalize_string)


class DispatchUnitSolutionSchema(MMSBase):
    _interval_field = "settlementdate"
    _primary_keys: List[str] = ["settlementdate", "duid"]

    settlementdate: datetime
    duid: str
    initialmw: Optional[float]

    _validate_duid = validator("duid")(normalize_duid)
    _validate_initialmw = validator("initialmw")(clean_float)


class TradingPriceSchema(MMSBase):
    _interval_field = "settlementdate"
    _primary_keys: List[str] = ["settlementdate", "regionid"]

    settlementdate: datetime
    runno: int
    regionid: str
    periodid: int
    rrp: float
    eep: int
    invalidflag: int
    lastchanged: datetime
    rop: float
    raise6secrrp: float
    raise6secrop: float
    raise60secrrp: float
    raise60secrop: float
    raise5minrrp: float
    raise5minrop: float
    raiseregrrp: float
    raiseregrop: float
    lower6secrrp: float
    lower6secrop: float
    lower60secrrp: float
    lower60secrop: float
    lower5minrrp: float
    lower5minrop: float
    lowerregrrp: float
    lowerregrop: float
    price_status: str


class TradingInterconnectorRes(MMSBase):
    _interval_field = "settlementdate"
    _primary_keys: List[str] = ["settlementdate", "interconnectorid"]

    settlementdate: datetime
    runno: int
    interconnectorid: str
    periodid: int
    meteredmwflow: float
    mwflow: float
    mwlosses: float
    lastchanged: datetime


class DispatchInterconnectorRes(MMSBase):
    _interval_field = "settlementdate"
    _primary_keys: List[str] = ["settlementdate", "interconnectorid"]

    settlementdate: datetime
    runno: int
    interconnectorid: str
    dispatchinterval: int
    intervention: int
    meteredmwflow: float
    mwflow: float
    mwlosses: float
    marginalvalue: float
    violationdegree: float
    lastchanged: datetime
    exportlimit: float
    importlimit: float
    marginalloss: float
    exportgenconid: str
    importgenconid: str
    fcasexportlimit: float
    fcasimportlimit: float
    local_price_adjustment_export: float
    locally_constrained_export: float
    local_price_adjustment_import: float
    locally_constrained_import: float


class DispatchPriceSchema(MMSBase):
    _interval_field = "settlementdate"
    _primary_keys: List[str] = ["settlementdate", "regionid"]

    settlementdate: datetime
    runno: int
    regionid: str
    dispatchinterval: int
    intervention: int
    rrp: float
    eep: int
    rop: float
    apcflag: int
    marketsuspendedflag: int
    lastchanged: datetime
    raise6secrrp: float
    raise6secrop: float
    raise60secrrp: float
    raise60secrop: float
    raise5minrrp: float
    raise5minrop: float
    raiseregrrp: float
    raiseregrop: float
    lower6secrrp: float
    lower6secrop: float
    lower60secrrp: float
    lower60secrop: float
    lower5minrrp: float
    lower5minrop: float
    lowerregrrp: float
    lowerregrop: float
    price_status: str


class DispatchRegionSum(MMSBase):
    _interval_field = "settlementdate"
    _primary_keys: List[str] = ["settlementdate", "regionid"]

    settlementdate: datetime
    runno: int
    regionid: str
    dispatchinterval: int
    intervention: int
    lastchanged: datetime

    totaldemand: float
    availablegeneration: float
    availableload: float
    demandforecast: float
    dispatchablegeneration: float
    dispatchableload: float
    netinterchange: float
    excessgeneration: float

    demand_and_nonschedgen: float


class DispatchUnitScada(MMSBase):
    _interval_field = "settlementdate"
    _primary_keys: List[str] = ["settlementdate", "duid"]

    settlementdate: datetime
    duid: str
    scadavalue: float


class MeterDataGenDUID(MMSBase):
    _interval_field = "interval_datetime"
    _primary_keys: List[str] = ["interval_datetime", "duid"]

    interval_datetime: datetime
    duid: str
    mwh_reading: float


class RooftopForecast(MMSBase):
    _interval_field = "interval_datetime"
    _primary_keys: List[str] = ["interval_datetime", "regionid"]

    interval_datetime: datetime
    lastchanged: datetime
    regionid: str
    powermean: float
    powerpoe50: float
    powerpoelow: float
    powerpoehigh: float


class RooftopActual(MMSBase):
    _interval_field = "interval_datetime"
    _primary_keys: List[str] = ["interval_datetime", "regionid"]

    interval_datetime: datetime
    lastchanged: datetime
    regionid: str
    power: float
    qi: float
    type: str


# Map AEMO full table names to schemas
TABLE_TO_SCHEMA_MAP = {
    "PARTICIPANT_REGISTRATION_MNSP_INTERCONNECTOR": ParticipantMNSPInterconnector,
    "MARKET_CONFIG_INTERCONNECTOR": MarketConfigInterconnector,
    "DISPATCH_UNIT_SOLUTION": DispatchUnitSolutionSchema,
    "TRADING_PRICE": TradingPriceSchema,
    "TRADING_INTERCONNECTORRES": TradingInterconnectorRes,
    "DISPATCH_INTERCONNECTORRES": DispatchInterconnectorRes,
    "DISPATCH_PRICE": DispatchPriceSchema,
    "DISPATCH_REGIONSUM": DispatchRegionSum,
    "DISPATCH_UNIT_SCADA": DispatchUnitScada,
    "METER_DATA_GEN_DUID": MeterDataGenDUID,
    "ROOFTOP_FORECAST": RooftopForecast,
    "ROOFTOP_ACTUAL": RooftopActual,
}


def get_mms_schema_for_table(table_name: str) -> Optional[MMSBase]:
    if table_name.upper() not in TABLE_TO_SCHEMA_MAP.keys():
        logger.warn("No schema found for table: {}".format(table_name))
        return None

    return TABLE_TO_SCHEMA_MAP[table_name.upper()]  # type: ignore
