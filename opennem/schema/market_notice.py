from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AEMOMarketNoticeType(Enum):
    load_shed = "LOAD SHED"
    load_restore = "LOAD RESTORE"
    inter_regional_transfer = "INTER-REGIONAL TRANSFER"
    reserve_notice = "RESERVE NOTICE"
    market_systems = "MARKET SYSTEMS"
    reclassify_contingency = "RECLASSIFY CONTINGENCY"
    non_conformance = "NON-CONFORMANCE"
    general_notice = "GENERAL NOTICE"
    market_intervention = "MARKET INTERVENTION"
    settlements_residue = "SETTLEMENTS RESIDUE"
    prices_unchanged = "PRICES UNCHANGED"
    prices_subject_to_review = "PRICES SUBJECT TO REVIEW"
    power_system_events = "POWER SYSTEM EVENTS"


class AEMOMarketNoticeSchema(BaseModel):
    id: int
    notice_type: AEMOMarketNoticeType
    creation_date: datetime = Field(description="The creation date of the notice")
    issue_date: datetime
    external_reference: str
    reason: str


class AEMOMarketNoticeResponseSchema(BaseModel):
    notices: list[AEMOMarketNoticeSchema]
