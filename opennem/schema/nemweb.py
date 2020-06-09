from pydantic import BaseModel


class Facility(BaseModel):
    NAME: str


class DISPATCH_UNIT_SCADA(BaseModel):
    SETTLEMENTDATE: int
    DUID: Facility
